
filename = 'phillipp1.data';
delimiter = ' ';
fileID = fopen(filename,'r');
formatSpec = '%f%f%f%f%f%f%f%f%f%f%[^\n\r]';
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter, 'MultipleDelimsAsOne', true, 'EmptyValue' ,NaN, 'ReturnOnError', false);
fclose(fileID);
phillipp1 = [dataArray{1:end-1}];
clearvars filename delimiter formatSpec fileID dataArray ans;

A = phillipp1(2:11,:);
b = phillipp1(13,:)';
z = phillipp1(15,:)';

bit = 32;
figure; hold all;
for i = 4:10
    T = mytypes('fixed',bit,bit-i);
    %T = mytypes('double');
    Afp = cast(A,'like',T);
    bfp = cast(b,'like',T);
    it = 10;
    Xfp = cgdfp2(Afp,bfp,it,T);
    Xfp2db = double(Xfp);
    err = sqrt(sum((double(Xfp) - z*ones(1,10)).^2,1));
    plot(log10(err));
end;
