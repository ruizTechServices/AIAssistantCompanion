# AI Assistant Companion

This Flask application generates AI-powered worksheets and stores worksheet metadata in Postgres.

## Environment Variables

Create a `.env` file with the following variables:

- `OPENAI_API_KEY`: API key for OpenAI models.
- `SESSION_SECRET`: secret key for Flask sessions.
- `DATABASE_URL`: PostgreSQL connection string (from Supabase or other host).
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID.
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret.
- `GOOGLE_REDIRECT_URL` (optional): OAuth redirect URI for local development.
- `SUPABASE_URL`: URL of your Supabase project.
- `SUPABASE_SERVICE_KEY`: Service role key for Supabase (used for storage uploads).

If you integrate Pinecone, also add:

- `PINECONE_API_KEY`: Pinecone API key.
- `PINECONE_ENV`: Pinecone environment region name.

## Supabase and Pinecone

The application connects to a Supabase Postgres database via `DATABASE_URL` and uploads generated worksheets to the `worksheets` storage bucket. Pinecone can be enabled to store text embeddings.
