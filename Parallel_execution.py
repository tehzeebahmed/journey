# example demonstrating **parallel execution** in a real-life scenario 
# with **error handling, retries, and recovery strategies**. 


### Scenario:
# Imagine a system that processes multiple data sources in parallel 
# (e.g., fetching data from APIs), with retry logic on failure 
# and a fallback recovery strategy.

# Import necessary libraries

# concurrent.futures provides a high-level interface for asynchronously executing callables.
# We use ThreadPoolExecutor to run tasks in parallel threads.
from concurrent.futures import ThreadPoolExecutor, as_completed

# time module helps us add delays between retries.
import time

# random module simulates occasional failures in API calls.
import random

# logging module helps us log info, warnings, and errors for monitoring.
import logging

# Configure logging to display time, level, and message.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define a function to simulate fetching data from an API.
def fetch_data_from_api(source_name: str) -> str:
    """
    Simulates an API call that may fail randomly.
    Args:
        source_name (str): Name of the data source.
    Returns:
        str: Simulated data string.
    Raises:
        Exception: Simulated failure.
    """
    logging.info(f"Starting fetch for {source_name}")
    # Simulate random failure with 30% chance.
    if random.random() < 0.3:
        raise Exception(f"API error occurred for {source_name}")
    # Simulate processing time.
    time.sleep(random.uniform(0.5, 1.5))
    data = f"Data from {source_name}"
    logging.info(f"Successfully fetched data from {source_name}")
    return data

# Define a retry decorator to handle retries with delay.
def retry(max_retries=3, delay=2):
    """
    Decorator to retry a function on exception.
    Args:
        max_retries (int): Maximum retry attempts.
        delay (int): Delay between retries in seconds.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logging.warning(f"Attempt {attempts} failed: {e}")
                    if attempts == max_retries:
                        logging.error(f"Max retries reached for {args[0]}")
                        raise
                    logging.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        return wrapper
    return decorator

# Wrap the fetch function with retry logic.
@retry(max_retries=3, delay=2)
def fetch_data_with_retry(source_name: str) -> str:
    return fetch_data_from_api(source_name)

# Define a recovery function to provide fallback data if all retries fail.
def recovery_strategy(source_name: str) -> str:
    logging.info(f"Applying recovery strategy for {source_name}")
    # Return default or cached data as fallback.
    return f"Default data for {source_name}"

# Main function to run parallel data fetching with error handling.
def main():
    # List of data sources to fetch from.
    data_sources = ["API_1", "API_2", "API_3", "API_4"]

    # Dictionary to store results.
    results = {}

    # Use ThreadPoolExecutor to run fetches in parallel threads.
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all fetch tasks to the executor.
        future_to_source = {
            executor.submit(fetch_data_with_retry, source): source
            for source in data_sources
        }

        # Process completed futures as they finish.
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                # Get result from future; this will raise if fetch failed after retries.
                data = future.result()
            except Exception as e:
                # If all retries failed, apply recovery strategy.
                logging.error(f"Fetching failed for {source}: {e}")
                data = recovery_strategy(source)
            # Store the data (either fetched or recovered).
            results[source] = data

    # Print all results.
    logging.info("All data fetching tasks completed. Results:")
    for source, data in results.items():
        print(f"{source}: {data}")

# Run the main function when script is executed.
if __name__ == "__main__":
    main()


"""

---

### Explanation:

- **Libraries:**
  - `concurrent.futures`: For parallel execution using threads.
  - `time`: To add delays between retries.
  - `random`: To simulate random failures.
  - `logging`: To log progress, warnings, and errors.

- **fetch_data_from_api** simulates an API call that randomly fails 30% of the time.

- **retry decorator** wraps any function to retry it up to a max number of times with delays between attempts.

- **fetch_data_with_retry** is the fetch function wrapped with retry logic.

- **recovery_strategy** provides fallback data if all retries fail.

- **main**:
  - Defines multiple data sources.
  - Uses `ThreadPoolExecutor` to fetch data from all sources in parallel.
  - Handles exceptions by applying recovery strategy.
  - Collects and prints results.

---

"""