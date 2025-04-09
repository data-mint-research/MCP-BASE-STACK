/**
 * LLM Manager for LibreChat
 *
 * This module provides functions to manage LLMs through the MCP protocol.
 * It handles model selection, routing, and specialized agent behavior.
 *
 * Compliant with MCP 2025-03-26 specification.
 */

const axios = require('axios');

// Configuration
const config = {
  mcpAdapterUrl: process.env.MCP_ADAPTER_URL || 'http://mcp-adapter:8001',
  ollamaUrl: process.env.OLLAMA_API_HOST || 'http://ollama:11434',
  models: {
    mistral: 'mistral:7b',
    deepseekCoder: 'deepseek-coder:6.7b',
    commandRp: 'command-rp:latest'
  },
  mcp: {
    protocol_version: '2025-03-26',
    client_id: 'librechat-llm-manager'
  }
};

// Initialize MCP client
const mcpClient = {
  async callTool(toolName, args) {
    console.log(`Calling MCP tool: ${toolName} with args:`, args);
    try {
      const response = await axios.post(
        `${config.mcpAdapterUrl}/api/tools/${toolName}`,
        args
      );
      return response.data;
    } catch (error) {
      console.error(`Error calling MCP tool ${toolName}:`, error.message);
      throw new Error(`MCP tool execution failed: ${error.message}`);
    }
  },
  
  async getResource(uri) {
    console.log(`Fetching MCP resource: ${uri}`);
    try {
      const response = await axios.get(
        `${config.mcpAdapterUrl}/api/resources/${uri.replace('file://', '')}`
      );
      return response.data.content;
    } catch (error) {
      console.error(`Error fetching MCP resource ${uri}:`, error.message);
      throw new Error(`MCP resource fetch failed: ${error.message}`);
    }
  }
};

/**
 * SERJ Agent class
 * Implements the SERJ (Specialized Expert Reasoning JSON) agent architecture
 * using MCP for tool access and resource management
 */
class SERJAgent {
  constructor() {
    this.primaryModel = config.models.mistral;
    this.codeModel = config.models.deepseekCoder;
    this.commandModel = config.models.commandRp;
    this.mcpClient = mcpClient;
  }

  /**
   * Process a user message through the SERJ agent
   *
   * @param {string} message - User message
   * @param {object} options - Processing options
   * @returns {Promise<object>} - Response from the agent
   */
  async processMessage(message, options = {}) {
    console.log('SERJ Agent processing message:', message);
    
    try {
      // Determine if this is a coding task
      const isCodingTask = this.isCodingRelated(message);
      
      if (isCodingTask) {
        console.log('Detected coding task, routing to MINTYcoder via MCP');
        return this.routeToCodingExpert(message);
      } else {
        console.log('Using primary model for general conversation');
        return this.useGeneralModel(message);
      }
    } catch (error) {
      console.error('Error in SERJ Agent:', error);
      return {
        response: `I encountered an error processing your request: ${error.message}. Please try again.`,
        source: 'SERJ (error)'
      };
    }
  }

  /**
   * Check if a message is related to coding
   * 
   * @param {string} message - User message
   * @returns {boolean} - True if coding related
   */
  isCodingRelated(message) {
    const codingKeywords = [
      'code', 'function', 'programming', 'algorithm', 'javascript',
      'python', 'java', 'c++', 'typescript', 'html', 'css', 'react',
      'angular', 'vue', 'node', 'express', 'api', 'database', 'sql'
    ];
    
    return codingKeywords.some(keyword => 
      message.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  /**
   * Route a message to the coding expert (MINTYcoder) via MCP
   *
   * @param {string} message - User message
   * @returns {Promise<object>} - Response from MINTYcoder
   */
  async routeToCodingExpert(message) {
    try {
      // Use MCP client to call MINTYcoder tool
      const mintycodeResult = await this.mcpClient.callTool('mintycoder', {
        prompt: message,
        language: 'auto-detect'
      });
      
      // Process the response through the primary model for better presentation
      return this.enhanceCodeResponse(mintycodeResult);
    } catch (error) {
      console.error('Error routing to coding expert via MCP:', error);
      return this.useGeneralModel(
        `I tried to process your coding request but encountered an error: ${error.message}. Let me try to answer more generally. ${message}`
      );
    }
  }

  /**
   * Enhance a code response with the primary model
   *
   * @param {object} codeResult - Result from MINTYcoder
   * @returns {Promise<object>} - Enhanced response
   */
  async enhanceCodeResponse(codeResult) {
    try {
      // Format the code result for the primary model
      const prompt = `
        I need to present this code solution to a user in a helpful way.
        
        Code: ${codeResult.code}
        
        Explanation: ${codeResult.explanation}
        
        Please provide a well-formatted response that includes the code (in a code block)
        and a clear, detailed explanation of how it works and how to use it.
      `;
      
      // Call the primary model through Ollama with MCP headers
      const response = await axios.post(
        `${config.ollamaUrl}/api/generate`,
        {
          model: this.primaryModel,
          prompt: prompt,
          stream: false
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'MCP-Client-ID': config.mcp.client_id,
            'MCP-Protocol-Version': config.mcp.protocol_version
          }
        }
      );
      
      return {
        response: response.data.response,
        source: 'SERJ via MCP/MINTYcoder',
        protocol: 'MCP 2025-03-26'
      };
    } catch (error) {
      console.error('Error enhancing code response:', error);
      return {
        response: `Here's the code solution:\n\n\`\`\`\n${codeResult.code}\n\`\`\`\n\n${codeResult.explanation}`,
        source: 'MCP/MINTYcoder (direct)',
        protocol: 'MCP 2025-03-26'
      };
    }
  }

  /**
   * Use the general model for non-coding tasks
   *
   * @param {string} message - User message
   * @returns {Promise<object>} - Response from the general model
   */
  async useGeneralModel(message) {
    try {
      const response = await axios.post(
        `${config.ollamaUrl}/api/generate`,
        {
          model: this.primaryModel,
          prompt: message,
          stream: false
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'MCP-Client-ID': config.mcp.client_id,
            'MCP-Protocol-Version': config.mcp.protocol_version
          }
        }
      );
      
      return {
        response: response.data.response,
        source: 'SERJ via MCP',
        protocol: 'MCP 2025-03-26'
      };
    } catch (error) {
      console.error('Error using general model:', error);
      return {
        response: 'I apologize, but I encountered an error processing your request. Please try again.',
        source: 'SERJ (error)',
        protocol: 'MCP 2025-03-26'
      };
    }
  }
}

/**
 * LLM Manager class
 * Provides functions to manage LLMs
 */
class LLMManager {
  constructor() {
    this.serj = new SERJAgent();
  }

  /**
   * Get available models using MCP protocol
   *
   * @returns {Promise<Array>} - List of available models
   */
  async getAvailableModels() {
    try {
      const response = await axios.get(
        `${config.ollamaUrl}/api/tags`,
        {
          headers: {
            'MCP-Client-ID': config.mcp.client_id,
            'MCP-Protocol-Version': config.mcp.protocol_version
          }
        }
      );
      return response.data.models || [];
    } catch (error) {
      console.error('Error getting available models via MCP:', error);
      return Object.values(config.models);
    }
  }

  /**
   * Process a message with a specific model using MCP protocol
   *
   * @param {string} message - User message
   * @param {string} model - Model to use
   * @param {object} options - Processing options
   * @returns {Promise<object>} - Response from the model
   */
  async processWithModel(message, model, options = {}) {
    console.log(`Processing message with model: ${model} via MCP`);
    
    if (model === 'agent-SERJ') {
      return this.serj.processMessage(message, options);
    }
    
    try {
      const response = await axios.post(
        `${config.ollamaUrl}/api/generate`,
        {
          model: model,
          prompt: message,
          stream: false
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'MCP-Client-ID': config.mcp.client_id,
            'MCP-Protocol-Version': config.mcp.protocol_version
          }
        }
      );
      
      return {
        response: response.data.response,
        source: `${model} via MCP`,
        protocol: 'MCP 2025-03-26'
      };
    } catch (error) {
      console.error(`Error processing with model ${model} via MCP:`, error);
      return {
        response: `I apologize, but I encountered an error while using the ${model} model. Please try again or select a different model.`,
        source: `${model} (error)`,
        protocol: 'MCP 2025-03-26'
      };
    }
  }
}

// Export the LLM Manager
module.exports = new LLMManager();
