-- Converge cart_items to the source-attribution schema (task 10.7).
--
-- Migration 0001 gained these columns after some local databases were already
-- initialized, and CREATE TABLE IF NOT EXISTS silently skips existing tables.
-- This migration brings any database — old volume or fresh — to one schema.
-- NOT VALID grandfathers pre-attribution rows while enforcing new writes.

ALTER TABLE cart_items ADD COLUMN IF NOT EXISTS restaurant_id TEXT;
ALTER TABLE cart_items ADD COLUMN IF NOT EXISTS restaurant_name TEXT;
ALTER TABLE cart_items ADD COLUMN IF NOT EXISTS brand_name TEXT;
ALTER TABLE cart_items ADD COLUMN IF NOT EXISTS source_label TEXT;

ALTER TABLE cart_items DROP CONSTRAINT IF EXISTS cart_items_source_attribution;
ALTER TABLE cart_items ADD CONSTRAINT cart_items_source_attribution CHECK (
    (
        vertical = 'food'
        AND restaurant_id IS NOT NULL
        AND restaurant_name IS NOT NULL
    )
    OR (
        vertical = 'instamart'
        AND source_label IS NOT NULL
    )
) NOT VALID;
