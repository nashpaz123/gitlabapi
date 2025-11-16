#!/bin/sh
# Service script that receives keywords and executes the appropriate function

# Read input from stdin or command line arguments
if [ $# -eq 0 ]; then
    # Read from stdin
    read -r input
    set -- $input
fi

# Parse the command
command="$1"

case "$command" in
    grant_role)
        if [ $# -ne 4 ]; then
            echo '{"success": false, "message": "grant_role requires 3 arguments: username, repository_or_group, role"}'
            exit 1
        fi
        python3 /usr/local/bin/gitlab_api.py grant_role "$2" "$3" "$4"
        ;;
    get_items)
        if [ $# -ne 3 ]; then
            echo '{"success": false, "message": "get_items requires 2 arguments: item_type (mr|issues), year"}'
            exit 1
        fi
        python3 /usr/local/bin/gitlab_api.py get_items "$2" "$3"
        ;;
    *)
        echo '{"success": false, "message": "Unknown command. Available commands: grant_role, get_items"}'
        echo "Usage:"
        echo "  grant_role <username> <repository_or_group> <role>"
        echo "  get_items <mr|issues> <year>"
        exit 1
        ;;
esac

