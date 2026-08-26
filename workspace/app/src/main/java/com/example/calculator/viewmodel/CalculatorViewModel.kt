package com.example.calculator.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.example.calculator.domain.CalculatorEngine
import com.example.calculator.domain.CalculatorEngine.EvalResult

/**
 * ViewModel for the calculator UI.
 *
 * It holds the current expression as a string and the latest result.
 * All UI actions are funneled through this class.
 */
class CalculatorViewModel : ViewModel() {

    private val _expression = MutableLiveData<String>("")
    val expression: LiveData<String> = _expression

    private val _result = MutableLiveData<String>("")
    val result: LiveData<String> = _result

    /** Append a digit or decimal point to the expression. */
    fun onDigit(digit: Char) {
        if (digit !in "0123456789.") return
        _expression.value = (_expression.value ?: "") + digit
    }

    /** Append an operator (+, -, *, /) to the expression. */
    fun onOperator(op: Char) {
        if (op !in "+-*/") return
        val current = _expression.value ?: ""
        if (current.isEmpty()) return // prevent leading operator
        // Disallow two consecutive operators
        if (current.last() in "+-*/") {
            // replace the previous operator
            _expression.value = current.dropLast(1) + op
        } else {
            _expression.value = current + op
        }
    }

    /** Clear the whole expression and result. */
    fun onClear() {
        _expression.value = ""
        _result.value = ""
    }

    /** Evaluate the current expression using the engine. */
    fun onEquals() {
        val expr = _expression.value ?: ""
        when (val eval = CalculatorEngine.evaluate(expr)) {
            is EvalResult.Success -> {
                // Trim trailing .0 for integer results
                val formatted = if (eval.value % 1.0 == 0.0) {
                    eval.value.toLong().toString()
                } else {
                    eval.value.toString()
                }
                _result.value = formatted
            }
            is EvalResult.Error -> {
                _result.value = "Error"
            }
        }
    }
}
