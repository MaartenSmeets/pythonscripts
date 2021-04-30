import stylecloud
import os
from stop_words import get_stop_words

stop_words = get_stop_words('english')

for filename in os.listdir("."):
        if filename.endswith(".txt"):
            print("Processing "+filename)
            outputfile=filename.replace(".txt",".png")
            stylecloud.gen_stylecloud(file_path=filename,
                                  icon_name= "fas fa-circle",
                                  background_color='white',
                                  output_name=outputfile,
                                  size=(800, 800),
                                  custom_stopwords=stop_words)
