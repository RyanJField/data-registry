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



## Django
