# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3

class VorysPipeline:
    def __init__(self):
        self.con = sqlite3.connect('sourav.db')

        self.cur = self.con.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS vorysdata(
                         name TEXT,
                         position TEXT,
                         location TEXT,
                         email TEXT,
                        UNIQUE(name,location,email)  
                          ) 
                         """)
        # self.con.commit()
    def process_item(self, item, spider):
        
        try:
                name = str(item['name']).strip().lower()
                position = str(item['position']).strip()
                location = str(item['location']).strip().lower()
                email = str(item['email']).strip().lower()

                # Skip ONLY if all fields are empty
                if not any([name, position, location, email]):
                    pass

                self.cur.execute("""
                    INSERT INTO vorysdata (name, position, location, email)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(name, location, email)
                    DO UPDATE SET
                        position = excluded.position
                """, (name, position, location, email))

                self.con.commit()
        except sqlite3.Error as e:
            spider.logger.error(f"DB error: {e}")
    
        return item
