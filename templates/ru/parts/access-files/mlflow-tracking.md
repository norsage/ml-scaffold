{{#if infra.mlflow_login}}

   Файл с правами 600 создаётся так, секция вписывается в редакторе; если
   в файле уже есть другие секции, новая дописывается в конец:

   ```bash
   mkdir -p ~/.mlflow && chmod 700 ~/.mlflow && touch ~/.mlflow/credentials && chmod 600 ~/.mlflow/credentials
   ```

   ```ini
   [mlflow]
   mlflow_tracking_username = <логин на сервере MLflow>
   mlflow_tracking_password = <пароль>
   ```
{{/if}}
