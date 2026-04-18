// C:\nxtturn\frontend\cypress\e2e\password-reset.cy.ts

describe('Password Reset Flow', () => {
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
      cy.contains('Success', { timeout: 15000 }).should('be.visible')

      // --- PHASE 2: RESET ---
      cy.testSetup('get_password_reset_link', { email: resetUser.email }).then((response) => {
        const resetUrl = response.body.link
        cy.visit(resetUrl)

        const newPassword = 'NewlyChangedPassword@456'
        cy.get('#new_password1').clear().type(newPassword)
        cy.get('#new_password2').clear().type(newPassword)

        cy.intercept('POST', '**/api/auth/password/reset/confirm/').as('passwordResetConfirm')
        cy.get('button[type="submit"]').click()

        cy.wait('@passwordResetConfirm', { timeout: 12000 }).then((interception) => {
          if (!interception.response) throw new Error('No response from backend')
          expect(interception.response.statusCode).to.equal(200)
        })

        // Confirm success message is shown on the UI
        cy.contains(/password has been set|successfully/i, { timeout: 15000 }).should('be.visible')

        // --- PHASE 3: VERIFY LOGIN (THE FINAL CHECK) ---

        // 1. Programmatic login with the NEW password
        cy.login(resetUser.username, newPassword)

        // 2. Force navigation to the root to trigger a fresh app load
        cy.visit('/')

        // 3. Verify the URL is no longer in the /auth/ section
        cy.url({ timeout: 20000 }).should('not.include', '/auth/')

        // 4. Robust Text Search: Look for "Home Feed" anywhere on the page
        // We remove the 'h2' restriction to make it more flexible
        cy.contains(/Home Feed/i, { timeout: 20000 }).should('be.visible')
      })
    })
  })
})
