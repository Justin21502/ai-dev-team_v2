package com.example.calculator.domain

import com.example.calculator.domain.CalculatorEngine.EvalResult
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Nested
import org.junit.jupiter.api.Test

class CalculatorEngineTest {

    @Nested
    @DisplayName("Expression evaluation")
    inner class Evaluation {

        @Test
        fun `simple addition`() {
            val result = CalculatorEngine.evaluate("2+3")
            assertThat(result).isInstanceOf(EvalResult.Success::class.java)
            val value = (result as EvalResult.Success).value
            assertThat(value).isEqualTo(5.0)
        }

        @Test
        fun `operator precedence`() {
            val result = CalculatorEngine.evaluate("2+3*4")
            assertThat(result).isInstanceOf(EvalResult.Success::class.java)
            val value = (result as EvalResult.Success).value
            assertThat(value).isEqualTo(14.0)
        }

        @Test
        fun `parentheses override precedence`() {
            val result = CalculatorEngine.evaluate("(2+3)*4")
            assertThat(result).isInstanceOf(EvalResult.Success::class.java)
            val value = (result as EvalResult.Success).value
            assertThat(value).isEqualTo(20.0)
        }

        @Test
        fun `division by zero yields error`() {
            val result = CalculatorEngine.evaluate("5/0")
            assertThat(result).isInstanceOf(EvalResult.Error::class.java)
            val message = (result as EvalResult.Error).message
            assertThat(message).contains("Division by zero")
        }

        @Test
        fun `invalid expression yields error`() {
            val result = CalculatorEngine.evaluate("2++2")
            assertThat(result).isInstanceOf(EvalResult.Error::class.java)
        }

        @Test
        fun `empty expression yields error`() {
            val result = CalculatorEngine.evaluate("")
            assertThat(result).isInstanceOf(EvalResult.Error::class.java)
        }
    }

    @Nested
    @DisplayName("Helper operations")
    inner class Helpers {

        @Test
        fun `add helper`() {
            assertThat(CalculatorEngine.add(1.5, 2.5)).isEqualTo(4.0)
        }

        @Test
        fun `sub helper`() {
            assertThat(CalculatorEngine.sub(5.0, 3.0)).isEqualTo(2.0)
        }

        @Test
        fun `mul helper`() {
            assertThat(CalculatorEngine.mul(4.0, 2.5)).isEqualTo(10.0)
        }

        @Test
        fun `div helper success`() {
            val result = CalculatorEngine.div(9.0, 3.0)
            assertThat(result).isInstanceOf(EvalResult.Success::class.java)
            val value = (result as EvalResult.Success).value
            assertThat(value).isEqualTo(3.0)
        }

        @Test
        fun `div helper division by zero`() {
            val result = CalculatorEngine.div(9.0, 0.0)
            assertThat(result).isInstanceOf(EvalResult.Error::class.java)
            val message = (result as EvalResult.Error).message
            assertThat(message).contains("Division by zero")
        }
    }
}
