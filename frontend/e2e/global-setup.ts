// Playwright global setup
// Add any global setup needed before tests run

export default async function globalSetup() {
  console.log('🚀 Starting E2E test suite');
  
  // You can add setup like:
  // - Database seeding
  // - Starting mock services
  // - Creating test users
  
  // Example: Verify backend is running
  try {
    const response = await fetch('http://localhost:8000/docs');
    if (!response.ok) {
      console.warn('⚠️  Backend might not be running on http://localhost:8000');
    } else {
      console.log('✓ Backend is accessible');
    }
  } catch (error) {
    console.warn('⚠️  Could not connect to backend. Make sure it is running.');
  }
}
