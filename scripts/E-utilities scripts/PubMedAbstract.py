# I used bio python to download pubmed abstracts 

Because I got an error after trying the code on the terminal 

 

[hlnrezae@login01 Pubmed_abstracts]$ esearch -db pubmed -query '("Osteoarthritis"[Mesh] OR Osteoarthritis) AND (mouse OR mice OR rat OR rats OR pig OR pigs OR rabbit OR rabbits) AND "English"[Language] NOT "Review"[Publication Type]' | efetch -format abstract > all_abstracts_texts.txt 

 

# I made a nano file called  

nano download_abstracts.py 

On this directory 

[hlnrezae@login01 LLM_Project]$ cd Pubmed_abstracts/ 

 

I used gemini for this nano file except the query and e-utilities commands parts  

 

 from Bio import Entrez 

import time 

 Entrez.email ="hlnrezae@liverpool.ac.uk" 

query = '("Osteoarthritis"[Mesh] OR Osteoarthritis) AND (mouse OR mice OR rat OR rats OR pig OR pigs OR rabbit OR rabbits) AND "English"[Language] NOT "Review"[Publication Type]' 

print("Searching PubMed...") 

handle = Entrez.esearch(db="pubmed", term=query, retmax=100000)  

record = Entrez.read(handle) 

handle.close() 

pmids = record["IdList"] 

print(f"Found {len(pmids)} articles.") 

with open("all_abstracts_texts.txt", "w", encoding="utf-8") as outfile: 

    batch_size = 200 

    for start in range(0, len(pmids), batch_size): 

        end = min(len(pmids), start + batch_size) 

        batch_pmids = pmids[start:end] 

        try: 

            fetch_handle = Entrez.efetch(db="pubmed", id=",".join(batch_pmids), rettype="abstract", retmode="text") 

            data = fetch_handle.read() 

            fetch_handle.close() 

            outfile.write(data) 

            outfile.write("\n" + "="*80 + "\n\n") 

            time.sleep(1)  

            print(f"Downloaded {end} out of {len(pmids)} abstracts") 

        except Exception as e: 

            print("all saved to all_abstracts_texts.txt") 