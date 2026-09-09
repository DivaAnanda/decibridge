/**
 * Demo credentials are printed on the login and landing pages so reviewers can
 * sign in without provisioning. That is acceptable for a demonstration deploy
 * and unacceptable for a pilot carrying real hospital data, so it is a build
 * flag rather than something to remember to delete.
 *
 * Set VITE_SHOW_DEMO_CREDENTIALS=false for any deploy that is not a demo.
 */
export const SHOW_DEMO_CREDENTIALS =
  import.meta.env.VITE_SHOW_DEMO_CREDENTIALS !== 'false'
