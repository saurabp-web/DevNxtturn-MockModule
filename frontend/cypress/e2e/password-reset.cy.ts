// C:\nxtturn\frontend\cypress\e2e\auth\password-reset.cy.ts

describe('Password Reset Flow', () => {
  const resetUser = {
    username: `reset_user_${Date.now()}`,
    email: `reset_${Date.now()}@cypresstest.com`,
    password: 'NewStrongPassword!789', // A strong password that meets Django's requirements
  }

  before(() => {
    // Seed the database with the test user
    cy.testSetup('create_user', resetUser)
  })

  context('on a standard viewport', () => {
    beforeEach(() => {
      cy.viewport('macbook-15')
    })

    it('successfully requests a reset and confirms the password can be changed', () => {
      // 1. Navigate to the password reset request page
      cy.visit('/auth/forgot-password')
      cy.get('h2').should('contain', 'Forgot Your Password?')

      // Type the email and click submit
      cy.get('#email').type(resetUser.email)

      // Intercept the POST request to the password reset API
      cy.intercept('POST', '/api/auth/password/reset/').as('passwordResetRequest')
      cy.get('button[type="submit"]').click()

      // Wait for the backend request to complete and verify success
      cy.wait('@passwordResetRequest', { timeout: 10000 })
        .its('response.statusCode')
        .should('eq', 200)

      // Assert that the success message appears on the UI
      cy.get('.bg-green-100, .text-green-600', { timeout: 15000 }) // Use broader selector and longer timeout
        .should('be.visible')
        .and('contain.text', 'Success')

      // 3. Obtain the password reset link directly from the backend's test utility
      cy.testSetup('get_password_reset_link', { email: resetUser.email }).then((response) => {
        const resetUrl = response.body.link

        // 4. Visit the reset link to access the password change form
        cy.visit(resetUrl)

        // Assert we are on the correct page before interacting with the form
        cy.url().should('include', '/auth/reset-password/')
        cy.get('h2').should('contain', 'Choose a New Password')

        // Enter the new password and confirm it
        const newPassword = 'AnotherStrongPassword@123' // A different strong password
        cy.get('#new_password1').type(newPassword)
        cy.get('#new_password2').type(newPassword)

        // Intercept and wait for the password reset confirmation request
        cy.intercept('POST', '/api/auth/password/reset/confirm/').as('passwordResetConfirm')
        cy.get('button[type="submit"]').click()
        cy.wait('@passwordResetConfirm', { timeout: 10000 })
          .its('response.statusCode')
          .should('eq', 200)

        // Confirm success message after password has been set
        cy.get('.bg-green-100, .text-green-600', { timeout: 15000 }).should(
          'contain.text',
          'Your password has been set.',
        )

        // Log in with the NEW password and assert successful redirect to Home Feed
        cy.login(resetUser.username, newPassword)
        cy.get('h2').should('contain', 'Home Feed') // Assert successful login
      })
    })
  })
})
