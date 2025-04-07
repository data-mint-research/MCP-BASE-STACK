# Data Backup and Recovery

This guide explains how to back up and restore data from the MCP-BASE-STACK components.

## Backing up LibreChat Data

LibreChat stores conversation history and user data in MongoDB. To back up this data:

```bash
# Create a backup directory with today's date
mkdir -p backups/$(date +%Y%m%d)

# Backup MongoDB data
docker exec chat-mongodb mongodump --out /tmp/mongo-backup
docker cp chat-mongodb:/tmp/mongo-backup backups/$(date +%Y%m%d)/mongo-backup
```

## Backing up Knowledge Graph

The Knowledge Graph contains the relationships between components and features. Regularly back up this data:

```bash
# Copy Knowledge Graph data to backup directory
cp -r kg/data backups/$(date +%Y%m%d)/kg-data
```

## Backing up Configuration Files

Important configuration files should also be backed up:

```bash
# Create a config backup directory
mkdir -p backups/$(date +%Y%m%d)/config

# Back up LibreChat configuration
cp LibreChat/.env backups/$(date +%Y%m%d)/config/
cp LibreChat/librechat.yaml backups/$(date +%Y%m%d)/config/

# Back up MCP Server configuration
cp mcp_requirements.txt backups/$(date +%Y%m%d)/config/
cp start_mcp_server.sh backups/$(date +%Y%m%d)/config/
```

## Backing up Model Files (Optional)

If you've made custom modifications to models, you might want to back them up:

```bash
# Create a models backup directory
mkdir -p backups/$(date +%Y%m%d)/models

# Back up Ollama model information
docker exec ollama ollama list > backups/$(date +%Y%m%d)/models/ollama-models-list.txt
```

## Automated Backups

You can automate backups using a cron job:

```bash
# Create a backup script
cat > backup_mcp_stack.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup MongoDB
docker exec chat-mongodb mongodump --out /tmp/mongo-backup
docker cp chat-mongodb:/tmp/mongo-backup $BACKUP_DIR/mongo-backup

# Backup Knowledge Graph
cp -r kg/data $BACKUP_DIR/kg-data

# Backup configs
mkdir -p $BACKUP_DIR/config
cp LibreChat/.env $BACKUP_DIR/config/
cp LibreChat/librechat.yaml $BACKUP_DIR/config/
cp mcp_requirements.txt $BACKUP_DIR/config/
cp start_mcp_server.sh $BACKUP_DIR/config/

# Log backup completion
echo "Backup completed at $(date)" >> backup_log.txt
EOF

# Make the script executable
chmod +x backup_mcp_stack.sh

# Add to crontab (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * cd /home/skr/projects/MCP-BASE-STACK && ./backup_mcp_stack.sh") | crontab -
```

## Restoring from Backup

### Restoring MongoDB Data

```bash
# Copy backup to container
docker cp backups/20250407/mongo-backup chat-mongodb:/tmp/

# Restore from backup
docker exec chat-mongodb mongorestore /tmp/mongo-backup
```

### Restoring Knowledge Graph

```bash
# Stop any processes that might be using the Knowledge Graph
kill $(cat mcp_server.pid)

# Restore Knowledge Graph data
cp -r backups/20250407/kg-data/* kg/data/

# Restart the MCP server
./start_mcp_server.sh
```

### Restoring Configuration Files

```bash
# Restore LibreChat configuration
cp backups/20250407/config/.env LibreChat/
cp backups/20250407/config/librechat.yaml LibreChat/

# Restart LibreChat to apply changes
cd LibreChat
docker compose down
docker compose up -d
```

## Backup Retention Policy

Consider implementing a backup retention policy:

- Keep daily backups for 7 days
- Keep weekly backups for 4 weeks
- Keep monthly backups for 6 months

You can automate this with a cleanup script that removes old backups based on their age.