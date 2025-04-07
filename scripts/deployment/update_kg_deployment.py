# update_kg_deployment.py
import networkx as nx

try:
    g = nx.read_graphml('core/kg/data/knowledge_graph.graphml')
    
    # Add deployment nodes
    deploy_dirs = [
      'deploy',
      'deploy/volumes'
    ]
    
    for dir_path in deploy_dirs:
      g.add_node(dir_path, type='directory', path=dir_path)
    
    # Add containment relationship
    g.add_edge('deploy', 'deploy/volumes', relation='contains')
    
    # Connect to root
    g.add_edge('project_root', 'deploy', relation='contains')
    
    # Add deployment file nodes
    deploy_files = [
      {'id': 'docker-compose.yml', 'path': 'deploy/docker-compose.yml', 'type': 'configuration'},
      {'id': 'docker-compose.dev.yml', 'path': 'deploy/docker-compose.dev.yml', 'type': 'configuration'},
      {'id': 'model-volumes.yml', 'path': 'deploy/volumes/model-volumes.yml', 'type': 'configuration'}
    ]
    
    for file in deploy_files:
      file_id = file['path']
      g.add_node(file_id, type=file['type'], name=file['id'], path=file['path'])
      parent_dir = file['path'].rsplit('/', 1)[0]
      g.add_edge(parent_dir, file_id, relation='contains')
    
    # Add service relationship with llm-server (renamed from ollama)
    llm_server_id = 'services/llm-server'
    if llm_server_id in g:
      # Add deployment relationship
      g.add_edge('deploy/docker-compose.yml', llm_server_id, relation='deploys')
      
      # Add renamed indicator if not already present
      if 'renamed_from' not in g.nodes[llm_server_id]:
        g.nodes[llm_server_id]['renamed_from'] = 'ollama'
    
    # Save updated graph
    nx.write_graphml(g, 'core/kg/data/knowledge_graph.graphml')
    print('Knowledge Graph updated with deployment structure')
except Exception as e:
    print(f"Error updating Knowledge Graph: {e}")