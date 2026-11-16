export type DeskNoticeStatus = 'cancelled' | 'rejected' | 'failed';

export interface DeskNotice {
  status: DeskNoticeStatus;
  heading: string;
  body: string;
}

const ENTITIES: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (character) => ENTITIES[character] ?? character);
}

// The holds desk as one page: the title being worked on and the notice
// for the last action. The stylesheet is `main/desk.css`, served beside it.
export function deskScreen(title: string, notice: DeskNotice): string {
  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head><meta charset="utf-8"><title>Holds desk</title><link rel="stylesheet" href="desk.css"></head>',
    '<body>',
    '<main class="desk">',
    `<h1>Holds desk: ${escapeHtml(title)}</h1>`,
    `<section class="notice notice--${notice.status}" role="status">`,
    `<h2>${escapeHtml(notice.heading)}</h2>`,
    `<p>${escapeHtml(notice.body)}</p>`,
    '<button type="button">Dismiss</button>',
    '</section>',
    '</main>',
    '</body>',
    '</html>',
  ].join('\n');
}
