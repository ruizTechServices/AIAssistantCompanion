# AI Assistant Companion

This Flask application generates AI-powered worksheets. It was initially designed to run on Replit and stores worksheet metadata in Postgres.

## Environment Variables

Create a `.env` file with the following variables:

- `OPENAI_API_KEY`: API key for OpenAI models.
- `SESSION_SECRET`: secret key for Flask sessions.
- `DATABASE_URL`: PostgreSQL connection string (from Supabase or other host).
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID.
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret.
- `REPLIT_DEV_DOMAIN` (optional): Dev domain for callback URL when running locally.

If you integrate Pinecone, also add:

- `PINECONE_API_KEY`: Pinecone API key.
- `PINECONE_ENV`: Pinecone environment region name.

## Removing Replit Specifics

- Delete `.replit` config and remove CSS references to `cdn.replit.com` in templates.
- Replace the Replit Postgres connection with your own database or Supabase.
- Update OAuth redirect URLs to your domain.
- Remove references to `REPLIT_DEV_DOMAIN` once deployed elsewhere.

## Supabase and Pinecone

To migrate, connect SQLAlchemy to the Supabase Postgres URL and configure Pinecone to store embeddings instead of the Postgres `embedding` array. Use Supabase Auth or Google OAuth for authentication.
