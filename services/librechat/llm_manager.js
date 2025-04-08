/**
 * LLM Manager for LibreChat
 * 
 * This module provides functions to manage LLMs through the MCP protocol.
 * It handles model selection, routing, and specialized agent behavior.
 */

const axios = require('axios');

// Configuration
const config = {
  mcpAdapterUrl: process.env.MCP_ADAPTER_URL || 'http://localhost:8001',
  ollamaUrl: process.env.OLLAMA_API_HOST || 'http://localhost:11434',
  models: {
    mistral: 'mistral:7b',
    deepseekCoder: 'deepseek-coder:6.7b',
    commandRp: 'command-rp:latest'
  }
};

/**
 * SERJ Agent class
 * Implements the SERJ (Specialized Expert Reasoning JSON) agent architecture
 */
class SERJAgent {
  constructor() {
    this.primaryModel = config.models.mistral;
    this.codeModel = config.models.deepseekCoder;
    this.commandModel = config.models.commandRp;
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
    
    // Determine if this is a coding task
    const isCodingTask = this.isCodingRelated(message);
    
    if (isCodingTask) {
      console.log('Detected coding task, routing to MINTYcoder');
      return this.routeToCodingExpert(message);
    } else {
      console.log('Using primary model for general conversation');
      return this.useGeneralModel(message);
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
   * Route a message to the coding expert (MINTYcoder)
   * 
   * @param {string} message - User message
   * @returns {Promise<object>} - Response from MINTYcoder
   */
  async routeToCodingExpert(message) {
    try {
      // Use MCP protocol to call MINTYcoder
      const response = await axios.post(
        `${config.mcpAdapterUrl}/api/tools/mintycoder`,
        {
          prompt: message,
          language: 'auto-detect'
        }
      );
      
      // Process the response through the primary model for better presentation
      const mintycodeResult = response.data;
      return this.enhanceCodeResponse(mintycodeResult);
    } catch (error) {
      console.error('Error routing to coding expert:', error);
      return this.useGeneralModel(
        `I tried to process your coding request but encountered an error. ${message}`
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
      
      // Call the primary model
      const response = await axios.post(
        `${config.ollamaUrl}/api/generate`,
        {
          model: this.primaryModel,
          prompt: prompt,
          stream: false
        }
      );
      
      return {
        response: response.data.response,
        source: 'SERJ via MINTYcoder'
      };
    } catch (error) {
      console.error('Error enhancing code response:', error);
      return {
        response: `Here's the code solution:\n\n\`\`\`\n${codeResult.code}\n\`\`\`\n\n${codeResult.explanation}`,
        source: 'MINTYcoder (direct)'
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
        }
      );
      
      return {
        response: response.data.response,
        source: 'SERJ'
      };
    } catch (error) {
      console.error('Error using general model:', error);
      return {
        response: 'I apologize, but I encountered an error processing your request. Please try again.',
        source: 'SERJ (error)'
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
   * Get available models
   * 
   * @returns {Promise<Array>} - List of available models
   */
  async getAvailableModels() {
    try {
      const response = await axios.get(`${config.ollamaUrl}/api/tags`);
      return response.data.models || [];
    } catch (error) {
      console.error('Error getting available models:', error);
      return Object.values(config.models);
    }
  }

  /**
   * Process a message with a specific model
   * 
   * @param {string} message - User message
   * @param {string} model - Model to use
   * @param {object} options - Processing options
   * @returns {Promise<object>} - Response from the model
   */
  async processWithModel(message, model, options = {}) {
    console.log(`Processing message with model: ${model}`);
    
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
        }
      );
      
      return {
        response: response.data.response,
        source: model
      };
    } catch (error) {
      console.error(`Error processing with model ${model}:`, error);
      return {
        response: `I apologize, but I encountered an error while using the ${model} model. Please try again or select a different model.`,
        source: `${model} (error)`
      };
    }
  }
}

// Export the LLM Manager
module.exports = new LLMManager();
