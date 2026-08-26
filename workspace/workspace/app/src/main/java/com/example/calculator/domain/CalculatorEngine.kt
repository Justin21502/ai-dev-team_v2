package com.example.calculator.domain

/**
 * Simple calculator engine that evaluates infix arithmetic expressions
 * containing +, -, *, / and decimal numbers.
 *
 * The engine is pure Kotlin and does not depend on Android classes,
 * making it easy to unit‑test.
 */
object CalculatorEngine {

    /** Result of an evaluation – either a successful Double or an error message. */
    sealed class EvalResult {
        data class Success(val value: Double) : EvalResult()
        data class Error(val message: String) : EvalResult()
    }

    /**
     * Evaluate a mathematical expression.
     *
     * @param expression a string such as "12+3.5*2"
     * @return [EvalResult] containing the computed value or an error.
     */
    fun evaluate(expression: String): EvalResult {
        if (expression.isBlank()) return EvalResult.Error("Empty expression")
        return try {
            val tokens = tokenize(expression)
            val rpn = shuntingYard(tokens)
            val result = evaluateRpn(rpn)
            EvalResult.Success(result)
        } catch (e: ArithmeticException) {
            EvalResult.Error(e.message ?: "Arithmetic error")
        } catch (e: IllegalArgumentException) {
            EvalResult.Error(e.message ?: "Invalid expression")
        }
    }

    // -------------------------------------------------------------------------
    // Tokenisation
    // -------------------------------------------------------------------------
    private sealed class Token {
        data class Number(val value: Double) : Token()
        data class Operator(val op: Char) : Token()
        object LeftParen : Token()
        object RightParen : Token()
    }

    private fun tokenize(expr: String): List<Token> {
        val tokens = mutableListOf<Token>()
        var i = 0
        while (i < expr.length) {
            when (val c = expr[i]) {
                in '0'..'9', '.' -> {
                    val start = i
                    while (i < expr.length && (expr[i].isDigit() || expr[i] == '.')) i++
                    val numberStr = expr.substring(start, i)
                    val number = numberStr.toDoubleOrNull()
                        ?: throw IllegalArgumentException("Invalid number: $numberStr")
                    tokens.add(Token.Number(number))
                    continue // already advanced i
                }
                '+', '-', '*', '/' -> tokens.add(Token.Operator(c))
                '(' -> tokens.add(Token.LeftParen)
                ')' -> tokens.add(Token.RightParen)
                ' ', '\t', '\n' -> { /* ignore whitespace */ }
                else -> throw IllegalArgumentException("Unexpected character: $c")
            }
            i++
        }
        return tokens
    }

    // -------------------------------------------------------------------------
    // Shunting‑yard algorithm – converts infix tokens to Reverse Polish Notation
    // -------------------------------------------------------------------------
    private fun shuntingYard(tokens: List<Token>): List<Token> {
        val output = mutableListOf<Token>()
        val opStack = ArrayDeque<Token>()

        fun precedence(op: Char) = when (op) {
            '+', '-' -> 1
            '*', '/' -> 2
            else -> throw IllegalArgumentException("Unknown operator: $op")
        }

        for (token in tokens) {
            when (token) {
                is Token.Number -> output.add(token)

                is Token.Operator -> {
                    while (opStack.isNotEmpty() &&
                        opStack.last() is Token.Operator &&
                        precedence((opStack.last() as Token.Operator).op) >= precedence(token.op)
                    ) {
                        output.add(opStack.removeLast())
                    }
                    opStack.addLast(token)
                }

                Token.LeftParen -> opStack.addLast(token)

                Token.RightParen -> {
                    while (opStack.isNotEmpty() && opStack.last() !is Token.LeftParen) {
                        output.add(opStack.removeLast())
                    }
                    if (opStack.isEmpty() || opStack.last() !is Token.LeftParen) {
                        throw IllegalArgumentException("Mismatched parentheses")
                    }
                    opStack.removeLast() // discard '('
                }
            }
        }

        while (opStack.isNotEmpty()) {
            val top = opStack.removeLast()
            if (top is Token.LeftParen || top is Token.RightParen) {
                throw IllegalArgumentException("Mismatched parentheses")
            }
            output.add(top)
        }

        return output
    }

    // -------------------------------------------------------------------------
    // Evaluate RPN
    // -------------------------------------------------------------------------
    private fun evaluateRpn(rpn: List<Token>): Double {
        val stack = ArrayDeque<Double>()
        for (token in rpn) {
            when (token) {
                is Token.Number -> stack.addLast(token.value)
                is Token.Operator -> {
                    if (stack.size < 2) throw IllegalArgumentException("Insufficient values")
                    val b = stack.removeLast()
                    val a = stack.removeLast()
                    val res = when (token.op) {
                        '+' -> a + b
                        '-' -> a - b
                        '*' -> a * b
                        '/' -> {
                            if (b == 0.0) throw ArithmeticException("Division by zero")
                            a / b
                        }
                        else -> throw IllegalArgumentException("Unknown operator: ${token.op}")
                    }
                    stack.addLast(res)
                }
                else -> throw IllegalArgumentException("Unexpected token in RPN")
            }
        }
        if (stack.size != 1) throw IllegalArgumentException("Malformed expression")
        return stack.last()
    }

    // -------------------------------------------------------------------------
    // Simple helper operations – useful for isolated unit tests
    // -------------------------------------------------------------------------
    fun add(a: Double, b: Double) = a + b
    fun sub(a: Double, b: Double) = a - b
    fun mul(a: Double, b: Double) = a * b
    fun div(a: Double, b: Double): EvalResult =
        if (b == 0.0) EvalResult.Error("Division by zero")
        else EvalResult.Success(a / b)
}
