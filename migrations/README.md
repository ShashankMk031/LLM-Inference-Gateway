"""
Two-Step Migration for APIKey.owner_id Column
==============================================

This directory contains SQL migration scripts to safely add the owner_id
foreign key to the api_keys table when existing data may be present.

Migration Order:

1. Run `001_add_owner_id_nullable.sql` - Adds nullable column with FK/index
2. Run backfill (manual or via script) - See step 2 in the SQL file
3. Run `002_make_owner_id_not_null.sql` - Alters column to NOT NULL

IMPORTANT: If api_keys table is empty, you can skip directly to step 3.
"""
