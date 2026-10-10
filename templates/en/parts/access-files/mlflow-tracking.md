{{#if infra.mlflow_login}}

   The file is created mode 600 like this, and the section is written in
   an editor; if the file has other sections already, the new one goes at
   the end:

   ```bash
   mkdir -p ~/.mlflow && chmod 700 ~/.mlflow && touch ~/.mlflow/credentials && chmod 600 ~/.mlflow/credentials
   ```

   ```ini
   [mlflow]
   mlflow_tracking_username = <login on the MLflow server>
   mlflow_tracking_password = <password>
   ```
{{/if}}
