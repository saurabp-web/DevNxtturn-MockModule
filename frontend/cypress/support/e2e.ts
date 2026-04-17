import './commands'

function cleanupDatabase() {
  cy.request({
    method: 'POST',
    url: '/api/test/setup/',
    body: { action: 'cleanup' },
    failOnStatusCode: false,
  })
}

before(() => {
  cleanupDatabase()
})

after(() => {
  cleanupDatabase()
})
