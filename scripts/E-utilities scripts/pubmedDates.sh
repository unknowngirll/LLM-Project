#!/bin/bash 

PROJECT_DIR="$HOME/OA_LLM_Project/scripts" 

OUTPUT_DIR="$PROJECT_DIR/data" 

mkdir -p $OUTPUT_DIR 

  

XTRACT="/home/nilla_/edirect/xtract" 

  

download_pmids_year_only() { 

    local SPECIES=$1 

    local OUTFILE=$OUTPUT_DIR/${SPECIES}_PMIDs_year.txt 

     

    echo "Downloading $SPECIES PMIDs with year..." 

     

    esearch -db pubmed \ 

        -query "(osteoarthritis) AND ($SPECIES) AND \"English\"[Language] NOT \"Review\"[Publication Type]" \ 

        | efetch -format xml \ 

        | $XTRACT -pattern PubmedArticle \ 

          -element PMID,PubDate/Year \ 

        > $OUTFILE 

     

    echo "$SPECIES: $(wc -l < $OUTFILE) records" 

} 

  

echo "Starting download..." 

download_pmids_year_only "Mouse" 

download_pmids_year_only "Rat" 

download_pmids_year_only "Pig" 

download_pmids_year_only "Rabbit" 

  

echo "" 

echo "Combining all PMIDs..." 

cat $OUTPUT_DIR/Mouse_PMIDs_year.txt \ 

    $OUTPUT_DIR/Rat_PMIDs_year.txt \ 

    $OUTPUT_DIR/Pig_PMIDs_year.txt \ 

    $OUTPUT_DIR/Rabbit_PMIDs_year.txt \ 

    | sort -u > $OUTPUT_DIR/All_PMIDs_year.txt 

  

echo "Total unique records: $(wc -l < $OUTPUT_DIR/All_PMIDs_year.txt)" 

echo "File saved: $OUTPUT_DIR/All_PMIDs_year.txt"