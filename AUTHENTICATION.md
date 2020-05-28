# GitHub auth setup

## Register an OAuth App in GitHub
* In the appropriate GitHub organization, as a user with admin rights, select the **Settings** tab.
* On the LHS menu, select **OAuth Apps** in **Developer settings**.
* Click **New OAuth App**. Add the following information:
  * **Application name**: this can be anything
  * **Homepage URL**: set this to `https://data.scrc.uk/`, for example
  * **Authorization callback URL**: set this to `https://data.scrc.uk/accounts/github/login/callback/`, for example
* Click **Register Application**
* The provided **Client ID** and **Client Secret** will be required later



## Django setup
* Login to the admin page, e.g. https://data.scrc.uk/admin, as superuser
* Select **Sites** and edit the **Display name** and **Domain name** so they are set correctly to the external URL (e.g. data.scrc.uk). Save the changes
* Select **Social applications**.
* Select **Add social application**. Add the following information:
  * **Provider** should be set to `GitHub`
  * **Client id** should be set to the **Client ID** from the previous step above
  * **Secret key** should be set to the **Client Secret** from the previous step above
  * **Key** can be left empty
  * The site setup in the previous step should be set as the site
  * Save the changes

# REST API user perspective

## Create a GitHub personal access token
* Go to your GitHub profile page https://github.com/settings/profile
* Select **Developer settings** on the LHS menu
* Select **Personal access tokens**
* Click **Generate personal access token** with the following info:
  * Specify a name for the token in **Note**
  * Select **read:org**
  * Click **Generate token**
  
## Querying the REST API
You need to include a header of the form specifying the token:
```
Authorization: token <token>
```
Example request:
```
curl -i -X POST -H "Content-Type: application/json" -H "Authorization: token <token>" https://data.scrc.uk/api/model/
```
