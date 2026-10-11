alter table fines add column charge_id text;
update fines set charge_id = stripe_charge_id where stripe_charge_id is not null;
alter table fines drop column stripe_charge_id;
