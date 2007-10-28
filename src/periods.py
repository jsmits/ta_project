from datetime import datetime

days = [
        #datetime(2004, 2, 23, 0, 0), 
        #atetime(2004, 2, 24, 0, 0), 
        #datetime(2004, 2, 25, 0, 0), 
        #datetime(2004, 2, 26, 0, 0), 
        #datetime(2004, 2, 27, 0, 0),
        
        #datetime(2004, 3,  1, 0, 0), 
        #datetime(2004, 3,  2, 0, 0), 
        #datetime(2004, 3,  3, 0, 0), 
        #datetime(2004, 3,  4, 0, 0), 
        #datetime(2004, 3,  5, 0, 0),
    
        #datetime(2004, 3,  8, 0, 0), 
        #atetime(2004, 3,  9, 0, 0), 
        #datetime(2004, 3, 10, 0, 0), 
        #datetime(2004, 3, 11, 0, 0), 
        #datetime(2004, 3, 12, 0, 0),
        
        #datetime(2004, 3, 15, 0, 0), 
        #datetime(2004, 3, 16, 0, 0), 
        #datetime(2004, 3, 17, 0, 0), 
        #datetime(2004, 3, 18, 0, 0), 
        #datetime(2004, 3, 19, 0, 0),
        
        #datetime(2004, 3, 22, 0, 0), 
        #datetime(2004, 3, 23, 0, 0), 
        #datetime(2004, 3, 24, 0, 0), 
        #datetime(2004, 3, 25, 0, 0), 
        #datetime(2004, 3, 26, 0, 0),
        
        datetime(2004, 3, 29, 0, 0), 
        datetime(2004, 3, 30, 0, 0), 
        datetime(2004, 3, 31, 0, 0), 
        datetime(2004, 4,  1, 0, 0), 
        datetime(2004, 4,  2, 0, 0),
        
        #datetime(2004, 4,  5, 0, 0), 
        #datetime(2004, 4,  6, 0, 0), 
        #datetime(2004, 4,  7, 0, 0), 
        #datetime(2004, 4,  8, 0, 0), 
        # datetime(2004, 4,  9, 0, 0), # invalid ticks
        
        #datetime(2004, 4, 12, 0, 0), 
        #datetime(2004, 4, 13, 0, 0), 
        #datetime(2004, 4, 14, 0, 0), 
        #datetime(2004, 4, 15, 0, 0), 
        #datetime(2004, 4, 16, 0, 0),
        
        #datetime(2004, 4, 19, 0, 0), 
        #datetime(2004, 4, 20, 0, 0), 
        #datetime(2004, 4, 21, 0, 0), 
        #datetime(2004, 4, 22, 0, 0), 
        #datetime(2004, 4, 23, 0, 0),
        
        #datetime(2004, 4, 26, 0, 0), 
        #datetime(2004, 4, 27, 0, 0), 
        #datetime(2004, 4, 28, 0, 0), 
        #datetime(2004, 4, 29, 0, 0), 
        #datetime(2004, 4, 30, 0, 0),
        
        #datetime(2004, 5,  3, 0, 0), 
        #datetime(2004, 5,  4, 0, 0), 
        #datetime(2004, 5,  5, 0, 0), 
        #datetime(2004, 5,  6, 0, 0), 
        #datetime(2004, 5,  7, 0, 0),
        
        #datetime(2004, 5, 10, 0, 0), 
        #datetime(2004, 5, 11, 0, 0), 
        #datetime(2004, 5, 12, 0, 0), 
        #datetime(2004, 5, 13, 0, 0), 
        #datetime(2004, 5, 14, 0, 0),
        
        #datetime(2004, 5, 17, 0, 0), 
        #datetime(2004, 5, 18, 0, 0), 
        #datetime(2004, 5, 19, 0, 0), 
        #datetime(2004, 5, 20, 0, 0), 
        #datetime(2004, 5, 21, 0, 0),
        
        #datetime(2004, 5, 24, 0, 0), 
        #datetime(2004, 5, 25, 0, 0), 
        #atetime(2004, 5, 26, 0, 0), 
        #datetime(2004, 5, 27, 0, 0), 
        #datetime(2004, 5, 28, 0, 0),
        
        ##!datetime(2004, 5, 31, 0, 0)!, # unavailable
        #datetime(2004, 6,  1, 0, 0), 
        #datetime(2004, 6,  2, 0, 0), 
        #datetime(2004, 6,  3, 0, 0), 
        #datetime(2004, 6,  4, 0, 0),
        
        #datetime(2004, 6,  7, 0, 0), 
        #datetime(2004, 6,  8, 0, 0), 
        #datetime(2004, 6,  9, 0, 0), 
        #datetime(2004, 6, 10, 0, 0), 
        ##!datetime(2004, 6, 11, 0, 0)!, # unavailable
        
        #datetime(2004, 6, 14, 0, 0), 
        #datetime(2004, 6, 15, 0, 0), 
        #datetime(2004, 6, 16, 0, 0), 
        #datetime(2004, 6, 17, 0, 0), 
        #datetime(2004, 6, 18, 0, 0),
        
        datetime(2004, 6, 21, 0, 0), 
        datetime(2004, 6, 22, 0, 0), 
        datetime(2004, 6, 23, 0, 0), 
        datetime(2004, 6, 24, 0, 0), 
        datetime(2004, 6, 25, 0, 0),
        
        #datetime(2004, 6, 28, 0, 0), 
        #datetime(2004, 6, 29, 0, 0), 
        #datetime(2004, 6, 30, 0, 0), 
        #datetime(2004, 7,  1, 0, 0), 
        #datetime(2004, 7,  2, 0, 0),
        
        ##!datetime(2004, 7,  5, 0, 0)!, # unavailable
        #datetime(2004, 7,  6, 0, 0), 
        #datetime(2004, 7,  7, 0, 0), 
        #datetime(2004, 7,  8, 0, 0), 
        #datetime(2004, 7,  9, 0, 0),
        
        #datetime(2004, 7, 12, 0, 0), 
        #datetime(2004, 7, 13, 0, 0), 
        #datetime(2004, 7, 14, 0, 0), 
        #datetime(2004, 7, 15, 0, 0), 
        #datetime(2004, 7, 16, 0, 0),
        
        #datetime(2004, 7, 19, 0, 0), 
        #datetime(2004, 7, 20, 0, 0), 
        #datetime(2004, 7, 21, 0, 0), 
        #datetime(2004, 7, 22, 0, 0), 
        #datetime(2004, 7, 23, 0, 0),
        
        #datetime(2004, 7, 26, 0, 0), 
        #datetime(2004, 7, 27, 0, 0), 
        #datetime(2004, 7, 28, 0, 0), 
        #datetime(2004, 7, 29, 0, 0), 
        #datetime(2004, 7, 30, 0, 0),
        
        #datetime(2004, 8,  2, 0, 0), 
        #datetime(2004, 8,  3, 0, 0), 
        #datetime(2004, 8,  4, 0, 0), 
        #datetime(2004, 8,  5, 0, 0), 
        #datetime(2004, 8,  6, 0, 0),
        
        #datetime(2004, 8,  9, 0, 0), 
        #datetime(2004, 8, 10, 0, 0), 
        #datetime(2004, 8, 11, 0, 0), 
        #datetime(2004, 8, 12, 0, 0), 
        #datetime(2004, 8, 13, 0, 0),
    ]