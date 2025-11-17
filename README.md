GitLab EE 15.11.13 setup and test of an GitLab API solution for 1. granting roles to users 2. counting the issues and MRs for a sepcific year.

### 1. Start GitLab playground and populate it (or create projects)

```bash
./setup_gitlab.sh
```

This will:
- Download and start GitLab EE 15.11.13
- Expose it on `http://localhost`
- Wait for initialization (10-15 minutes)
- **Automatically retrieve and display the root password** when GitLab is ready

1. Open GitLab in your browser: http:/localhost"
2. Login as root (use password shown by './setup_gitlab.sh' or run docker exec -it gitlab bash -c 'cat /etc/gitlab/initial_root_password' | grep -i password)"

populate `http://localhost` with projects or by running the generator:

```bash
MY_GILAB_URL=http://localhost/ # http://host.docker.internal/ on a mac
cat > /tmp/gilab/gpt.json <<EOF
{
  "environment": {
    "name": "10k",
    "url": "http://localhost/",
    "user": "root",
    "config": {
      "latency": "0"
    },
    "storage_nodes": ["default"]
  },
  "gpt_data": {
    "root_group": "gpt",
    "large_projects": {
      "group": "large_projects",
      "project": "gitlabhq"
    },
    "many_groups_and_projects": {
      "group": "many_groups_and_projects",
      "subgroups": 10,
      "subgroup_prefix": "gpt-subgroup-",
      "projects": 5,
      "project_prefix": "gpt-project-"
    }
  }
}
EOF
nahshonp@MacBookPro ~ %

docker run -it -e ACCESS_TOKEN='glpat-xxxxx' -v /tmp/gilab/gpt.json:/tmp/gpt.json gitlab/gpt-data-generator "--environment=/tmp/gpt.json"
#Y when prompted to proceed[Y/N]
```

### 2. Create API Token

1. Open GitLab in your browser: "http:/localhost"
2. Login as root (use password shown by './setup_gitlab.sh' or run docker exec -it gitlab bash -c 'cat /etc/gitlab/initial_root_password' | grep -i password)"
3. Go to: http:/localhost/-/profile/personal_access_tokens"
 Or: Click your profile (top right) -> Edit Profile -> Access Tokens"

4. Create and copy new token with:"
   - Name: api-token (or any name you prefer)"
   - Scopes: Check 'api' and 'write_repository'"
   - Expiration: Set as needed (or leave blank for no expiration)"

5. Copy the token (it starts with 'glpat-')"

Then:
1. Open `http://localhost` in your browser, login as `root` 
3. Navigate to: `http://localhost/-/profile/personal_access_tokens`
4. Create a new token with:
   - Name: `api-token` (or any name)
   - Scopes: Check `api` and `write_repository`
   - Expiration: Optional
5. **Copy the token** (it starts with `glpat-`)

### 4. Set Environment Variables

```bash
export GITLAB_URL=http://localhost #http://host.docker.internal/ on a mac , see troubleshooting for netwroking options
export GITLAB_TOKEN=glpat-xxxxx  # Replace with your token
```

### 5. Build the api docker image

```bash
docker build -t gitlab-api . #set tag if versioning
```

## 6. Run Ctests

### Test grant_role function (nned to create the user first)

```bash
docker run --rm \
  -e GITLAB_URL=http://localhost \
  -e GITLAB_TOKEN=$GITLAB_TOKEN \
  gitlab-api grant_role root test-group/test-project Developer

#e.g docker run --rm -e GITLAB_URL='http://host.docker.internal' -e GITLAB_TOKEN='glpat-xxxxx' gitlab-api grant_role memyselfandi1 gpt/many_groups_and_projects/
{
  "success": true,
  "message": "Role granted successfully. User \"2\" now has \"Developer\" role on project \"4\""
}

```

### Test get_items function

```bash
docker run --rm \
  -e GITLAB_URL=http://localhost \
  -e GITLAB_TOKEN=$GITLAB_TOKEN \
  gitlab-api get_items issues 2025

#e.g docker run --rm -e GITLAB_URL='http://host.docker.internal' -e GITLAB_TOKEN='glpat-xxxxx' gitlab-api get_items issues 2025
{
  "success": true,
  "count": 1,
....
  "message": "Found 1 issues created in 2025"
}
```

### Test with stdin

```bash
echo "get_items issues 2025" | docker run --rm -i \
  -e GITLAB_URL=http://host.docker.internal \
  -e GITLAB_TOKEN=$GITLAB_TOKEN \
  gitlab-api
```

## Troubleshooting

### GitLab not accessible

Check if container is running:
```bash
docker ps | grep gitlab
```

Check logs:
```bash
docker logs gitlab -f
```

### API token not working

- Verify token has `api` and `write_repository` 
- Ensure token starts with `glpat-`
- Check token hasn't expired

### access errors
- On various machines localhost will not be available  for containers on the default docker ls network (Connection refused - connect(2) for "localhost" port 80). on mac/windows try http://host.docker.internal instead of http://localhost (or setup a network and ensuer all the project's containers are on it)

### Permission errors

- Ensure you're using a token with sufficient permissions
- For groups: need Maintainer or Owner role
- For projects: need Maintainer or Owner role

## Clean Up

To stop and remove GitLab:

```bash
docker stop gitlab
docker rm gitlab
```

To remove all GitLab data:

```bash
sudo rm -rf /tmp/gitlab
```

