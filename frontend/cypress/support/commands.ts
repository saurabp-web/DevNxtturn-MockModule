/// <reference types="cypress" />

Cypress.Commands.add('login', (username, password) => {
  const apiBase = '/api'
  // 1. Kill race conditions by intercepting the profile call
  cy.intercept('GET', `${apiBase}/auth/user/`).as('getUserProfile')

  // 2. Programmatic Login
  cy.request({
    method: 'POST',
    url: `${apiBase}/auth/login/`,
    body: { username, password },
  }).then(({ body }) => {
    window.localStorage.setItem('authToken', body.key)
    cy.visit('/')
    // 3. Wait for the app to be fully initialized
    cy.wait('@getUserProfile', { timeout: 10000 })
  })
})

Cypress.Commands.add('testSetup', (action, data = {}) => {
  return cy.request({
    method: 'POST',
    url: `/api/test/setup/`,
    body: { action, data },
  })
})

Cypress.Commands.add('logout', () => {
  window.localStorage.removeItem('authToken')
})

declare global {
  namespace Cypress {
    interface Chainable {
      login(username: string, password: string): Chainable<void>
      testSetup(action: string, data?: any): Chainable<Cypress.Response<any>>
      logout(): Chainable<void>
    }
  }
}
export {}
