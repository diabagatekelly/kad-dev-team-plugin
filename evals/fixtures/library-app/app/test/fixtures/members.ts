import type { Member } from '../../members/member';

export const smsMember: Member = {
  member_row_id: 4182,
  row_version: 3,
  created_at_utc: '2024-03-11T17:42:09.000Z',
  updated_at_utc: '2026-02-02T09:15:31.000Z',
  card_number: '21987004417263',
  full_name: 'Marisol Okafor-Brennan',
  email: 'marisol.okaforbrennan@gmail.com',
  phone: '+15032847716',
  postal_address: '1418 SE Alder St, Portland, OR 97214',
  status_code: 'A',
  contact_pref_code: 'S',
  membership_expires_utc: '2027-03-11T00:00:00.000Z',
};

export const postalMember: Member = {
  ...smsMember,
  member_row_id: 977,
  card_number: '21987001093358',
  full_name: 'Theodore Vance Whitcombe',
  email: 'tvwhitcombe@comcast.net',
  phone: null,
  postal_address: '7020 N Interstate Ave Apt 3B, Portland, OR 97217',
  contact_pref_code: 'P',
};
