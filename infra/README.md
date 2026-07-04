# EasyOrder Infrastructure

Local development uses PostgreSQL as the Supabase-compatible persistence base.

## PostgreSQL

Start the database:

```bash
make db-up
```

Check the connection:

```bash
docker compose -f infra/docker-compose.yml exec db psql -U easyorder -d easyorder -c "SELECT 1;"
```

Apply the session/cart schema, indexes, realtime publication hook, and RLS policies:

```bash
make db-migrate
```

Roll the migration back:

```bash
make db-rollback
```

Stop the database:

```bash
make db-down
```

## Optional Supabase Local Stack

Later slices can add Supabase CLI configuration for Auth, Realtime, and Storage. Until then,
the project keeps mock integrations as the default and uses plain PostgreSQL for local
schema and adapter work.

## WhatsApp API Testing

For testing WhatsApp Cloud API outbound messages using the credentials loaded from `src/backend/.env`:

```bash
# Check test phone number status
python3 scripts/test_whatsapp_api.py --check-number

# Send the hello_world template message (ensure recipient number is pre-verified on Meta dashboard)
python3 scripts/test_whatsapp_api.py --send-template --to <RECIPIENT_PHONE_NUMBER>
```

