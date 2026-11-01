import type { CancelHoldResult } from './cancel-hold';

/*
 * cancelNotice: the notice the desk screen shows after a cancel.
 *
 * Inputs: a CancelHoldResult (status, and a reason for rejected or failed).
 * Outputs: a CancelNotice with a heading, a body and ready-to-serve markup.
 *
 * The heading is picked by status; the body is the reason when there is
 * one, otherwise a fixed sentence. The markup is a section with the
 * heading, the body and a dismiss button, followed by the script that wires
 * the button and removes the notice after eight seconds.
 *
 * The next slice's route serves the markup as is; this module is the
 * single place the notice's shape lives.
 */

// The notice shown at the desk after a cancel.
export interface CancelNotice {
  // The heading of the notice.
  heading: string;
  // The body of the notice.
  body: string;
  // The markup for the desk screen.
  markup: string;
}

// Builds the notice for a result.
export function cancelNotice(result: CancelHoldResult): CancelNotice {
  // Pick the heading by status.
  const heading = result.status === 'cancelled' ? 'Hold cancelled' : 'Hold not cancelled';
  // Pick the body by reason.
  const body = result.reason ?? 'The member is no longer in the queue for this title.';
  // Build the markup.
  const markup = `
    <section class="notice notice--${result.status}">
      <h2>${heading}</h2>
      <p>${body}</p>
      <button type="button" data-dismiss>Dismiss</button>
    </section>
    <script>
      const notice = document.querySelector('.notice');
      const dismiss = notice.querySelector('[data-dismiss]');
      dismiss.addEventListener('click', () => {
        notice.remove();
      });
      setTimeout(() => notice.remove(), 8000);
    </script>
  `;
  // Return the notice.
  return { heading, body, markup };
}
