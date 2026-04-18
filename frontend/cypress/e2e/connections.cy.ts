// C:\nxtturn\frontend\cypress\e2e\connections.cy.ts

describe('Icon-Based Connection and Follow System', () => {
  // Use a constant for the API base path as defined by the Vite proxy
  const API_BASE_PATH = '/api'

  const userA = {
    username: 'userA_follower',
    password: 'password123',
    email: 'userA@cypresstest.com',
  }
  const userB = {
    username: 'userB_followed',
    password: 'password123',
    email: 'userB@cypresstest.com',
  }

  beforeEach(() => {
    // Ensure a clean slate and create users for each test
    // Chain user creation to prevent race conditions
    cy.testSetup('cleanup') // Ensure clean slate before each test, this must complete first.
    cy.testSetup('create_user', userA).then(() => {
      return cy.testSetup('create_user', userB)
    })
  })

  it('handles the full follow, connect, accept, and disconnect lifecycle via the new icon UI', () => {
    // === PART 1: User A logs in and visits User B's profile ===
    cy.login(userA.username, userA.password)

    // Set up intercept *before* visiting the page to ensure it catches the profile load
    cy.intercept('GET', `${API_BASE_PATH}/profiles/${userB.username}/`).as('getProfileB')
    cy.visit(`/profile/${userB.username}`)
    cy.wait('@getProfileB', { timeout: 15000 }) // Wait for User B's profile data to load

    // ASSERT 1: Initial state - Ensure buttons exist and are visible
    // FIX: Scroll element into view to handle overflow:hidden issues, then assert visibility
    cy.get('[data-cy="connect-button"]')
      .scrollIntoView()
      .should('be.visible')
      .and('contain', 'Connect')
    cy.get('[data-cy="follow-toggle-button"]')
      .scrollIntoView()
      .should('be.visible')
      .and('contain', 'Follow')
    cy.get('[data-cy="message-button"]').should('be.visible')

    // ACTION 1: User A clicks "Follow"
    cy.intercept('POST', `${API_BASE_PATH}/users/${userB.username}/follow/`).as('followUser')
    cy.intercept('GET', `${API_BASE_PATH}/profiles/${userB.username}/`).as(
      'getProfileB_AfterFollow',
    )
    cy.get('[data-cy="follow-toggle-button"]').click({ force: true }) // Force click to bypass clipping
    cy.wait(['@followUser', '@getProfileB_AfterFollow'], { timeout: 15000 })

    // ASSERT 2: Follow state is updated
    cy.get('[data-cy="follow-toggle-button"]').should('be.visible').and('contain', 'Following')
    cy.get('[data-cy="connect-button"]').should('be.visible')

    // ACTION 2: User A clicks "Connect"
    cy.intercept('POST', `${API_BASE_PATH}/connections/requests/`).as('sendRequest')
    cy.intercept('GET', `${API_BASE_PATH}/profiles/${userB.username}/`).as(
      'getProfileB_AfterConnect',
    )
    cy.get('[data-cy="connect-button"]').click({ force: true }) // Force click
    cy.wait(['@sendRequest', '@getProfileB_AfterConnect'], { timeout: 15000 })

    // ASSERT 3: Button state changes to "Pending"
    cy.get('[data-cy="pending-button"]').should('be.visible')
    cy.get('[data-cy="follow-toggle-button"]').should('be.visible').and('contain', 'Following')
    cy.logout()

    // === PART 2: User B logs in and accepts the request ===
    cy.login(userB.username, userB.password)

    cy.intercept('GET', `${API_BASE_PATH}/profiles/${userA.username}/`).as('getProfileA')
    cy.visit(`/profile/${userA.username}`)
    cy.wait('@getProfileA', { timeout: 15000 })

    // ASSERT 4: User B sees "Accept" icon
    cy.get('[data-cy="accept-request-button"]')
      .scrollIntoView()
      .should('be.visible')
      .and('contain', 'Accept')

    // ACTION 3: User B clicks "Accept"
    cy.intercept('POST', `${API_BASE_PATH}/users/${userA.username}/accept-request/`).as(
      'acceptRequest',
    )
    cy.intercept('GET', `${API_BASE_PATH}/profiles/${userA.username}/`).as(
      'getProfileA_AfterAccept',
    )
    cy.get('[data-cy="accept-request-button"]').click({ force: true }) // Force click
    cy.wait(['@acceptRequest', '@getProfileA_AfterAccept'], { timeout: 15000 })

    // ASSERT 5: Final connected state is visible
    cy.get('[data-cy="connected-button"]').should('be.visible')
    cy.get('[data-cy="follow-toggle-button"]').should('not.exist') // Should be replaced by connected button
    cy.get('[data-cy="message-button"]').should('be.visible')

    // === PART 3: User B disconnects from User A ===
    // ACTION 4: User B clicks the "Connected" icon to reveal disconnect option
    cy.get('[data-cy="connected-button"]').click({ force: true }) // Force click

    // ASSERT 6: The "Disconnect" button is visible
    cy.get('[data-cy="disconnect-button"]').should('be.visible')

    // ACTION 5: User B clicks "Disconnect"
    cy.intercept('DELETE', `${API_BASE_PATH}/users/${userA.username}/follow/`).as('disconnectUser')
    cy.intercept('GET', `${API_BASE_PATH}/profiles/${userA.username}/`).as(
      'getProfileA_AfterDisconnect',
    )
    cy.get('[data-cy="disconnect-button"]').click({ force: true }) // Force click
    cy.wait(['@disconnectUser', '@getProfileA_AfterDisconnect'], { timeout: 15000 })

    // ASSERT 7: State reverts to default - Ensure buttons are visible
    cy.get('[data-cy="connect-button"]').scrollIntoView().should('be.visible')
    cy.get('[data-cy="follow-toggle-button"]')
      .scrollIntoView()
      .should('be.visible')
      .and('contain', 'Follow')
  })
})
