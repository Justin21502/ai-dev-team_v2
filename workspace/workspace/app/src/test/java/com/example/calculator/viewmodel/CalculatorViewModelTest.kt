package com.example.calculator.viewmodel

import androidx.arch.core.executor.testing.InstantTaskExecutorExtension
import com.example.calculator.domain.CalculatorEngine
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith

@ExtendWith(InstantTaskExecutorExtension::class)
class CalculatorViewModelTest {

    private lateinit var viewModel: CalculatorViewModel

    @BeforeEach
    fun setUp() {
        viewModel = CalculatorViewModel()
    }

    @Test
    @DisplayName("Digit and operator input builds correct expression")
    fun `building expression`() {
        viewModel.onDigit('1')
        viewModel.onOperator('+')
        viewModel.onDigit('2')
        assertThat(viewModel.expression.value).isEqualTo("1+2")
    }

    @Test
    @DisplayName("Evaluation produces correct result")
    fun `evaluate simple expression`() {
        viewModel.onDigit('4')
        viewModel.onOperator('*')
        viewModel.onDigit('5')
        viewModel.onEquals()
        assertThat(viewModel.result.value).isEqualTo("20")
    }

    @Test
    @DisplayName("Clear resets expression and result")
    fun `clear works`() {
        viewModel.onDigit('9')
        viewModel.onOperator('-')
        viewModel.onDigit('3')
        viewModel.onEquals()
        viewModel.onClear()
        assertThat(viewModel.expression.value).isEmpty()
        assertThat(viewModel.result.value).isEmpty()
    }

    @Test
    @DisplayName("Consecutive operators replace previous one")
    fun `replace consecutive operator`() {
        viewModel.onDigit('5')
        viewModel.onOperator('+')
        viewModel.onOperator('-')
        assertThat(viewModel.expression.value).isEqualTo("5-")
    }

    @Test
    @DisplayName("Leading operator is ignored")
    fun `ignore leading operator`() {
        viewModel.onOperator('+')
        assertThat(viewModel.expression.value).isEmpty()
    }

    @Test
    @DisplayName("Division by zero shows error")
    fun `division by zero error`() {
        viewModel.onDigit('8')
        viewModel.onOperator('/')
        viewModel.onDigit('0')
        viewModel.onEquals()
        assertThat(viewModel.result.value).isEqualTo("Error")
    }
}
