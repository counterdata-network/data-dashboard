Deploying with Dokku
====================

One time setup:

1. create a new app: `dokku apps:create story-processor-dashboard`
2. link that app to the database: `dokku postgres:link story-processor-db story-processor-dashboard`
3. setup env vars: `dokku config:set story-processor-dashboard SENTRY_DSN=the_url FEMINICIDE_API_URL=the_url FEMINICIDE_API_KEY=the_key PROCESSOR_DB_URI=postgres://path`
4. redirect web requests: `dokku ports:add story-processor-dashboard http:80:8000`
5. add the remote to your local machine: `git remote add dfprod dokku@my-server:story-processor-dashboard`
6. push to the remote: `git push dfprod main`
