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

Stop the database:

```bash
make db-down
```

## Optional Supabase Local Stack

Later slices can add Supabase CLI configuration for Auth, Realtime, and Storage. Until then,
the project keeps mock integrations as the default and uses plain PostgreSQL for local
schema and adapter work.
