from sqlalchemy import create_engine
import mysql.connector
from mysql.connector import pooling
from processing_logs import MetricsCalculator, LogParser, Log
import os
import logging
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(), 
        ]
    )
logger= logging.getLogger(__name__)
class DatabaseManager:
    def __init__(self):
        logger.info("Initializing MySQL Connection Pool...")
        self.pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,  
            pool_reset_session=True,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        

    def get_connection(self):   
        logger.info("get connection from pool .. ")

        return self.pool.get_connection()
    
    def get_metric(self):
        result = None
        try:
            conn= self.get_connection()
            cursor= conn.cursor()
        except Exception as e:
            logger.error(f"Connection to database pool failed due to :{e}")
            return
        try:
            query = """
                    SELECT total_requests, error, avg_response
                    FROM metrics
                    """
            cursor.execute(query)
            result = cursor.fetchone()
        except Exception as e:
            logger.error(f"Get metrics failed due to : {e}")
        finally:
            cursor.close()
            conn.close()
            logger.info("connection closed")
        return result
    
    def update_metric(self, calc : MetricsCalculator):
        try:
            conn= self.get_connection()
            cursor= conn.cursor()
        except Exception as e:
            logger.error(f"Connection to database pool failed due to :{e}")
            return
        try:
            query_get = "SELECT total_requests, error, avg_response FROM metrics"
            cursor.execute(query_get)
            prev_results= cursor.fetchone()
            cursor.fetchall()

            if not prev_results:
                prev_requests, prev_errors, prev_avg= 0, 0, 0.0
            else:
                prev_requests, prev_errors, prev_avg= prev_results[0], prev_results[1], prev_results[2]

            new_requests= prev_requests + calc.total_requests
            new_errors= prev_errors + calc.errors

            prev_total_time= prev_avg * prev_requests
            new_total_time= prev_total_time + calc.total_response
            new_avg= new_total_time / new_requests if new_requests > 0 else 0.0


            query= """
                UPDATE metrics 
                SET total_requests = %s, error= %s, avg_response= %s 
                    """
            
            values= (new_requests, new_errors, new_avg)
            cursor.execute(query, values)

            conn.commit()
            logger.info("Metrics updated successfully.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update the metrics due to: {e}")
        finally:
            cursor.close()
            conn.close()
            logger.info("Connection closed ... ")

    def reset_metrics(self,calc: MetricsCalculator):
        try:
            conn= self.get_connection()
            cursor= conn.cursor()
        except Exception as e:
            logger.error(f"Connection to database pool failed due to :{e}")
            return
        try:
            query= """
                UPDATE metrics 
                SET total_requests = %s, error= %s, avg_response= %s 
                    """
            values= (0, 0, 0)
            cursor.execute(query, values)
            conn.commit()
            calc.reset_metrics_obj()
            logger.info("metrics reseted ..")
        except Exception as e:
            conn.rollback()
            logger.error(f"Reset failed due to : {e}")
        finally:
            cursor.close()
            conn.close()
            logger.info("Connection closed ... ")
            
    def update_component(self, calc : MetricsCalculator):
        
        try:
            conn= self.get_connection()
            cursor= conn.cursor()
        except Exception as e:
            logger.error(f"Connection to database pool failed due to :{e}")
            return
        try:
        
            for comp_name, comp_data in calc.components.items():
                if comp_data.requests == 0:
                    continue
                query= "SELECT requests, errors, avg_response FROM component_stats WHERE component = %s"
                cursor.execute(query, (comp_name,))
                row= cursor.fetchone()
                if row:
                    prev_req, prev_err, prev_avg= row

                    prev_total_time=prev_avg * prev_req
                    new_batch_total= comp_data.requests * comp_data.avg_response

                    new_req= prev_req + comp_data.requests
                    new_err= prev_err + comp_data.errors

                    new_total_time= new_batch_total +prev_total_time
                    new_avg= new_total_time / new_req if new_req > 0 else 0.0
                    query = """
                        UPDATE component_stats
                        SET requests = %s, errors= %s, avg_response= %s
                        WHERE component = %s
                        """
            
                    values= (new_req, new_err, new_avg, comp_name)
                    cursor.execute(query, values)
                else :
                    cursor.execute("""
                        INSERT INTO component_stats (component, requests, errors, avg_response) 
                        VALUES (%s, %s, %s, %s)
                    """, (comp_name, comp_data.requests, comp_data.errors, comp_data.avg_response))
            conn.commit()
            logger.info("update component done succesfully ..")
        except Exception as e:
            conn.rollback()
            logger.error(f"Update component failed due to : {e}")
        finally:
            cursor.close()
            conn.close()
            logger.info("Connection closed ... ")

    def get_components_stats(self):
        try:
            conn= self.get_connection()
            cursor= conn.cursor()
        except Exception as e:
            logger.error(f"Connection to database pool failed due to :{e}")
            return
        
        try:
            query= """
                SELECT component, requests, errors, avg_response FROM component_stats
                """
            cursor.execute(query)
            results= cursor.fetchall()            

        except Exception as e:
            conn.rollback()
            logger.error(f"get components failed due to {e}")
        finally:
            cursor.close()
            conn.close()
            logger.info("Connection closed ..")
        return results
