PROJECT_DIR="$HOME/OA_LLM_Project" 

OUTPUT_DIR="$PROJECT_DIR/data" 

mkdir -p "$OUTPUT_DIR" 

  

# list of species

# We will iterate through this list to download data for each species. 

SPECIES_LIST=("Mouse" "Rat" "Pig" "Rabbit")  

  

# --- Download function --- 

download_data() { 

    local SPECIES=$1 

    local OUTFILE=$OUTPUT_DIR/${SPECIES}_PMID_Dates.tsv 

    # Define the PubMed query for the current species 

    local QUERY="(osteoarthritis) AND ($SPECIES) AND \"English\"[Language] NOT \"Review\"[Publication Type]" 

  
    echo "Processing data for: $SPECIES" 



  

    # 1. Search for PMIDs and retrieve ESummary XML 

    # FIX for "Missing -db argument": Explicitly adding '-db pubmed' to esummary 

    esearch -db pubmed -query "$QUERY" \ 

        | esummary -db pubmed \ 

        | efetch -format xml > "$OUTPUT_DIR/${SPECIES}_summary.xml" # Save temporary XML summary file 

  

    # 2. Check the number of records 

    local PMID_COUNT=$(grep -c '<Id>' "$OUTPUT_DIR/${SPECIES}_summary.xml") 

  

    if [ "$PMID_COUNT" -eq 0 ]; then 

        echo "Found 0 PMIDs for $SPECIES. Skipping." 

        rm "$OUTPUT_DIR/${SPECIES}_summary.xml" 

        return 

    fi 

     

    echo " Found $PMID_COUNT PMIDs." 

  

    # 3. Extract PMID and Publication Date from the XML file 

    echo -e "PMID\tPubDate" > $OUTFILE # Add TSV header (PMID and PubDate) 

  

    # Use grep and sed to extract the relevant fields from the ESummary XML 

    grep -E '<Id>|<PubDate>' "$OUTPUT_DIR/${SPECIES}_summary.xml" | sed -n ' 

        /<PubDate Format="8">/ { 

            # Extract the date in the YYYY/MM/DD format 

            s/.*<PubDate Format="8">\([0-9-]*\).*/\1/ 

            h # Hold the extracted date 

        } 

        /<Id>/ { 

            # Extract the PMID 

            s/.*<Id>\(.*\)<\/Id>.*/\1/ 

            G # Append the held date 

            s/\n/\t/ # Replace Newline separator with Tab 

            p # Print the result (PMID \t PubDate) 

        } 

    ' | grep -v '^PMID' >> $OUTFILE  

  

    # 4. Cleanup and remove the temporary file 

    rm "$OUTPUT_DIR/${SPECIES}_summary.xml" 

     

    echo " Download complete for $SPECIES. Records saved to $OUTFILE" 

    echo "Total records: $(wc -l < $OUTFILE)" 

    echo "" 

} 

  

# --- Execute download for all species in the list --- 

for SPECIES in "${SPECIES_LIST[@]}"; do 

    download_data "$SPECIES" 

done 