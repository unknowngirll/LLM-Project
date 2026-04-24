#!/bin/bash 

# Script to download PubMed PMIDs for OA project 

# Date: 2025-11-09 

  

# directory to the outputs 

OUTPUT_DIR="$PROJECT_DIR/data" 

mkdir -p $OUTPUT_DIR 

  

# Function  for downloading the PMIDs 

download_pmids() { 

    local SPECIES=$1 

    local OUTFILE=$OUTPUT_DIR/${SPECIES}_PMIDs.txt 

  

    echo "Downloading $SPECIES PMIDs..." 

    esearch -db pubmed \ 

        -query "(osteoarthritis) AND ($SPECIES) AND \"English\"[Language] NOT \"Review\"[Publication Type]" \ 

        | efetch -format uid > $OUTFILE 

  

    echo "$SPECIES: $(wc -l < $OUTFILE) PMIDs" 

} 

  

#  downloading all the  PMIDs 

download_pmids "Mouse" 

download_pmids "Rat" 

download_pmids "Pig" 

download_pmids "Rabbit" 

  

#  all the PMIDs together 

echo "Combining all PMIDs..." 

cat $OUTPUT_DIR/Mouse_PMIDs.txt \ 

    $OUTPUT_DIR/Rat_PMIDs.txt \ 

    $OUTPUT_DIR/Pig_PMIDs.txt \ 

    $OUTPUT_DIR/Rabbit_PMIDs.txt \ 

    > $OUTPUT_DIR/all_species_PMIDs.txt 

  

# remove the  repeated pmids 

sort $OUTPUT_DIR/all_species_PMIDs.txt | uniq > $OUTPUT_DIR/unique_PMIDs.txt 

  

#total PMIDs 

echo "Total unique PMIDs:" 

wc -l $OUTPUT_DIR/unique_PMIDs.txt 

 

 

All these codes saved in this command line>>> nano download_pubmed_data.sh 