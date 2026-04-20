// C:\nxtturn\frontend\cypress\e2e\password-reset.cy.ts

describe('Password Reset Flow', () => {
  // This prevents the "postMessage" error from failing the test in Docker
  // It is a standard fix for headless Chromium runners.
  beforeEach(() => {
    cy.on('uncaught:exception', (err) => {
      if (err.message.includes('postMessage')) {
        return false
      }
    })
  })

  const resetUser = {
    username: `reset_user_${Date.now()}`,
    email: `reset_${Date.now()}@cypresstest.com`,
    password: 'InitialPassword@123',
  }

  before(() => {
    // Clean slate and create the user
    cy.testSetup('cleanup')
    cy.testSetup('create_user', resetUser)
  })

  context('on a standard viewport', () => {
    beforeEach(() => {
      cy.viewport('macbook-15')
    })

    it('successfully requests a reset and confirms the password can be changed', () => {
      // --- PHASE 1: REQUEST ---
      cy.visit('/auth/forgot-password')
      cy.get('#email').clear().type(resetUser.email)
      cy.intercept('POST', '**/api/auth/password/reset/').as('passwordResetRequest')
      cy.get('button[type="submit"]').click()
      cy.wait('@passwordResetRequest').its('response.statusCode').should('eq', 200)
      cy.contains('Check your email', { timeout: 15000 }).should('be.visible')

      // --- PHASE 2: RESET ---
      cy.testSetup('get_password_reset_link', { email: resetUser.email }).then((response) => {
        const resetUrl = response.body.link
        cy.visit(resetUrl)

        // HARDENING FIX: Wait for the "Verifying link" spinner to disappear
        // This ensures the input fields are actually on the screen before we type
        cy.get('#new_password1', { timeout: 10000 }).should('be.visible')

        const newPassword = 'NewlyChangedPassword@456'
        cy.get('#new_password1').type(newPassword)
        cy.get('#new_password2').type(newPassword)

        // Ensure button is enabled (Reactive logic check)
        cy.get('button[type="submit"]').should('not.be.disabled')

        cy.intercept('POST', '**/api/auth/password/reset/confirm/').as('passwordResetConfirm')
        cy.get('button[type="submit"]').click()

        cy.wait('@passwordResetConfirm', { timeout: 12000 })
          .its('response.statusCode')
          .should('eq', 200)

        // Confirm success message is shown on the UI
        cy.contains(/successfully/i, { timeout: 15000 }).should('be.visible')

        // --- PHASE 3: VERIFY LOGIN (THE FINAL CHECK) ---
        cy.login(resetUser.username, newPassword)
        cy.visit('/')
        cy.url({ timeout: 20000 }).should('not.include', '/auth/')
        cy.contains(/Home Feed/i, { timeout: 20000 }).should('be.visible')
      })
    })
  })
})
