#include "TFile.h"
#include "TTree.h"
#include "TString.h"
#include "TFile.h"

#include <string>
#include <sstream>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <ctype.h>
#include <bitset> 

using namespace std;

void Usage();
string replace_with_str(string str, string str_from, string str_to);

int main(int argc, char *argv[]){

  char *infile;
  string outfile;
  char line[200];

  unsigned long a,b,e;
  double c,d;
  unsigned long CHBIT,EDGEBIT,DATABIT,SWEEPBIT,TAGBIT;
  Double_t ch,edge,data,rtdata,sweepdata,tagdata,datalost;
  Int_t ChN;
  Double_t Caloff[4],Calfact[4];
  Int_t DataLength;

  //number of address of data
  CHBIT = 0x07;
  EDGEBIT = 0x08;
  DATABIT = 0xFFFFFFF0;
//  SWEEPBIT = 0xFFF000000000;
  SWEEPBIT = 0xFFFF00000000;
  TAGBIT = 0x7FFF000000000000;
  
  if(argc<=1){
    Usage();
    return -1;
  }
  else {
    infile = argv[1];
    string temp = string(argv[1]);
    //string oheader = replace_with_str(temp,"@","");    
    //outfile = replace_with_str(oheader,"lst","root");    
    outfile = replace_with_str(temp,"lst","root");    
    cout<<infile<<" -> "<<outfile<<endl;
  }
  

  ifstream ifs(infile);
  if(!ifs){
    cout<<"File can not open!"<<endl;
    return -1;
  }
  
  //TTree
  TFile *rootfile = new TFile(outfile.c_str(),"RECREATE");
  TTree *tree = new TTree("data","data");
  tree -> Branch ("ch", &ch, "ch/D");
  tree -> Branch ("edge", &edge, "edge/D");
  tree -> Branch ("data", &data, "data/D");
  tree -> Branch ("rtdata", &rtdata, "rtdata/D");
  tree -> Branch ("sweepdata", &sweepdata, "sweepdata/D");
  tree -> Branch ("tagdata", &tagdata,"tagdata/D");
  tree -> Branch ("datalost", &datalost, "datalost/D");

  Int_t loop=0;
  while(!ifs.eof()){
    ifs.getline(line,200);
    Int_t judge=isdigit(static_cast<unsigned char>(line[0]));
    if(judge==0){
      string Header(line, sizeof(line) / sizeof(line[0]));
      if(Header.substr(1,3)=="CHN"){
	string temp = Header.substr(4,1);
	sscanf(temp.c_str(),"%d",&ChN);
      }
      if(Header.substr(0,7)=="caloff="){
	string temp = Header.substr(7);
	sscanf(temp.c_str(), "%lf", &c);	
	Caloff[ChN]=c;
      }
      if(Header.substr(0,8)=="calfact="){
	string temp = Header.substr(8);
	sscanf(temp.c_str(), "%lf", &d);	
	Calfact[ChN]=d;
      }  
      if(Header.substr(0,12)==";datalength="){
	string temp = Header.substr(12,1);
	sscanf(temp.c_str(), "%ld", &e);	
	DataLength=e;
      }
//        printf("ChN = %d     caloff = %lf   calfact =  %lf    ;datalength = %ld\n",ChN,c,d,e);  
    }

    if(judge!=0){
      if(DataLength==4){
	a=strtol(line,NULL,16);
	
	ch = (a & CHBIT);
	edge = ((a & EDGEBIT)>>3);
	data = ((a >>4))*0.1;
	rtdata = data-Caloff[static_cast<int>(ch)];
	tree->Fill();
	
	loop ++;
      }
      else if(DataLength==6){
	a=strtol(line,NULL,16);
	
	ch = (a & CHBIT);
	edge = ((a & EDGEBIT)>>3);
	data = ((a & DATABIT)>>4)*0.1;
	rtdata = data-Caloff[static_cast<int>(ch)];
	sweepdata = (a >> 32);
	tree->Fill();
	
	loop ++;
      }
      else if(DataLength==8){
	a=strtol(line,NULL,16);
	
	ch = (a & CHBIT);
	edge = ((a & EDGEBIT)>>3);
	data = ((a & DATABIT)>>4)*0.1;
	rtdata = data-Caloff[static_cast<int>(ch)];
	sweepdata = ((a & SWEEPBIT)>>32);
	tagdata = ((a & TAGBIT)>>48);
	datalost = (a >> 63);
	printf("%.f    %.f      %.f      %.2f     %.2f\n",ch,tagdata,sweepdata,data,rtdata);
	tree->Fill();

	loop++;

      }
    }
  }
  ifs.close();  
  
  rootfile->Write();
  rootfile->Close();

  return 0;
  
}

void Usage(){
  cout<<"Please enter the convert file name!"<<endl;

}

string replace_with_str(string str, string str_from, string str_to){
  string::size_type pos = 0;
  pos=str.find(str_from,pos);
  str.replace(pos,str_from.length(),str_to);

  return str;
}


