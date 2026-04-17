// frontend/cypress/e2e/real_time_notifications.cy.ts

// Define simple types for our test data to satisfy TypeScript and improve autocompletion.
interface TestUser {
  username: string
  token: string
}

interface TestGroup {
  name: string
  slug: string
}

describe('Real-Time Notifications', () => {
  // Declare variables in the suite scope to be accessible in both `beforeEach` and `it`.
  let groupCreator: TestUser
  let groupRequester: TestUser
  let privateGroup: TestGroup

  beforeEach(() => {
    //
    // SETUP PHASE: Create all necessary data for the test in a clean environment.
    // This follows the project's convention of using a single backend endpoint for all test setup.
    //

    // 1. Clean the database to ensure a pristine state for this test run.
    // Chain cleanup to ensure it completes before any user creation.
    cy.testSetup('cleanup')
      .then(() => {
        // 2. Create the user who will own the group and RECEIVE the notification.
        return cy.testSetup('create_user', { username_prefix: 'creator' })
      })
      .then((response) => {
        groupCreator = response.body

        // 3. Create the user who will SEND the join request.
        return cy.testSetup('create_user', { username_prefix: 'requester' })
      })
      .then((response) => {
        groupRequester = response.body

        // 4. Create a private group owned by the 'creator' user.
        // Now, groupCreator.username is DEFINITELY available.
        return cy.testSetup('create_group', {
          creator_username: groupCreator.username, // Use the actual username from the response
          name: 'Real-Time Notifications Test Group',
          is_private: true,
          privacy_level: 'private', // Ensure it's explicitly private
        })
      })
      .then((response) => {
        privateGroup = response.body
      })
  })

  it('should display a notification indicator in real-time when a join request is received', () => {
    //
    // EXECUTION AND ASSERTION PHASE
    //

    // 1. Log in as the group creator, the user who will receive the notification.
    // The test assumes a default password for users created via the test setup utility.
    cy.login(groupCreator.username, 'Airtel@123')
    cy.visit('/')

    // 2. Assert the initial state. Before any action, the notification indicator
    //    should not be present in the DOM. This is a critical baseline.
    cy.get('[data-cy="notification-indicator"]').should('not.exist')

    // 3. Trigger the event from the background. The 'requester' user sends a join
    //    request. We use `cy.request` to do this via the API because it is
    //    faster and more reliable than simulating it through the UI.
    // --- FIX: Correct URL concatenation to remove double slash ---
    cy.request({
      method: 'POST',
      url: `/api/groups/${privateGroup.slug}/membership/`, // VITE_API_BASE_URL is /api/, so this forms /api/groups/...
      headers: {
        Authorization: `Token ${groupRequester.token}`,
      },
    })

    // 4. THE CRITICAL ASSERTION: Verify the UI updated automatically.
    //    We give Cypress a generous timeout because WebSocket messages can have a small delay.
    //    The test will wait up to 10 seconds for the element to appear.
    cy.get('[data-cy="notification-indicator"]', { timeout: 10000 })
      .should('be.visible') // It should now be visible...
      .and('contain.text', '1') // ...and it should contain the number 1.
  })
})
