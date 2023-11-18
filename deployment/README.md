# Encrypt

```commandline
ansible-vault encrypt --vault-password-file /path/to/vault.txt --output docker-compose.yaml.enc docker-compose.yaml
```

# Decrypt
```commandline
ansible-vault decrypt --vault-password-file /path/to/vault.txt --output docker-compose.yaml docker-compose.yaml.enc
```