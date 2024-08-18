
# gradio-okta demonstration

This demonstrates how to implement Okta OIDC authentication in a gradio app

It is a combination of the following documents
<https://www.gradio.app/guides/sharing-your-app#o-auth-with-external-providers>
and
<https://github.com/okta-samples/okta-flask-sample>

## 1. Create the Okta app and popultae .okta.env

Use the [The Okta CLI Tool](https://github.com/okta/okta-cli#installation) to creae an app. The command is: `okta apps create`

The following are the questions and responses required

- **Application name:** is the name of the app inside okta. Default will be parent directory name
- **Type of Application:** `Web` app configures the app to use Okta hosted html forms for user login, so we dont have to create them ourselves!
- **Framework of Application:** `Other` becuase this is python, we dont need a starter app.
- **Redirect URI(s):** `https://127.0.0.1/auth` to work locally. You'll need to add
  an addtional URI when you push the app to the cloud with a real dns name
- **Post Logout Redirect URI(s):** `http://127.0.0.1:8080/` to work locally. Again, you'll need to add to this list when you publish behind a real dns name

```shell
$ okta apps create                       

Application name [gradio-okta]: 
Type of Application
(The Okta CLI only supports a subset of application types and properties):
> 1: Web
> 2: Single Page App
> 3: Native App (mobile)
> 4: Service (Machine-to-Machine)
Enter your choice [Web]: 1
Framework of Application
> 1: Okta Spring Boot Starter
> 2: Spring Boot
> 3: JHipster
> 4: Quarkus
> 5: Other
Enter your choice [Other]: 5
Redirect URI
Common defaults:
 Quarkus OIDC - http://localhost:8080/callback
 JHipster - http://localhost:8080/login/oauth2/code/oidc
 Spring Security - http://localhost:8080/login/oauth2/code/okta
Enter your Redirect URI(s) [http://localhost:8080/callback]: http://127.0.0.1:8080/auth
Enter your Post Logout Redirect URI(s) [http://localhost:8080/]: http://127.0.0.1:8080/

Okta application configuration has been written to: /Users/brianpeterson/Projects/cloudshift/gradio-okta/.okta.env
```

### Okta authorization servers

Okta authorization servers handle token issuance and validation etc. There is always an "org authorization server" at the url
<https://{domain}.okta.org/oauth>. You can also create addtional "custom authorization servers" if you need customized behaviors.
A new Okta organization automatically has the org authorization server active at <https://{domain}.okta.org/oauth> and a
custom authorization server called "default" availble at <https://{domain}.okta.org/oauth/default>.

In my (limited) experience, the out of the box custom authorization server called "default" is enabled, but has not policy / rules
attached and as such, does not work for OIDC/OAuth authentication. Strangely however, the okta cli and most of the Okta
examples you find assume that you will use the custom authorization server called "default".

Solutions:

1. Change the urls to use the org auth server. IN the `.okta.env` created by the okta CLI, the line that defines `OKTA_OAUTH2_ISSUER`
   will be something like: `export OKTA_OAUTH2_ISSUER="https://dev-1234567.okta.com/oauth2/default"`. You can change this to
   `export OKTA_OAUTH2_ISSUER="https://dev-1234567.okta.com/oauth2"` (notice the removal of `/default` form the url). This
   will configure the app to use the org default authentication server which works out of the box
2. Modify the custom server called "default" to have a Policy and a rule. 

   1. Go to Admin console <https://dev-1234567-admin.okta.com/admin/dashboard>
   2. Go to Security > API > Authorization Servers > select "default" auth server
   3. Go to Access Polices > click "Add New Access Policy" (I called my "default")
   4. Click "Add Rule". I called mine "Catch ALL" and took the default settings.

## 2. Install poetry dependancies

```shell
poetry install
```

## 3. Run the app

```shell
poetry run app.py
```

The login to <http://127.0.0.1:8080> and login with a valid okta username in your instance.
