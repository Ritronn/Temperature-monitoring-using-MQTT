import { useEffect, useRef, useState } from 'react';

/**
 * Custom hook for managing WebSocket connections with automatic reconnection.
 * 
 * @param {string} url - The WebSocket URL to connect to
 * @returns {Object} { isConnected: boolean, lastMessage: any }
 * 
 * Requirements: 5.2, 10.1, 10.5, 10.6, 20.3
 */
export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    // Function to establish WebSocket connection
    const connect = () => {
      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        // Handle connection open event
        ws.onopen = () => {
          setIsConnected(true);
          console.log('WebSocket connected');
        };

        // Handle incoming messages
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        // Handle errors
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        // Handle connection close event
        ws.onclose = () => {
          setIsConnected(false);
          console.log('WebSocket disconnected');

          // Attempt reconnection after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        
        // Attempt reconnection after 3 seconds on connection failure
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      }
    };

    // Establish initial connection
    connect();

    // Cleanup function
    return () => {
      // Clear reconnection timeout if it exists
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // Close WebSocket connection if it exists
      if (wsRef.current) {
        // Remove event handlers to prevent reconnection attempts during cleanup
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url]);

  return { isConnected, lastMessage };
}
