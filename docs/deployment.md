Deploying with Dokku
====================

One time setup:

1. create a new app: `dokku apps:create story-processor-dashboard`
2. add the remote to your local machien: `git remote add dfprod dokku@my-server:story-processor-dashboard`
3. push to the remote: `git push dfprod main`
