clear;

d = 500;
cmin = 1.2;
cmax = 10;
bs = [0 32];
ibit = 10;
it = 15;
its = [4 8 15];
R = 20;
sigmaY = 0.1;

%results = struct('r',{},'d',{},'nmult',{},'n',{},'kappa',{},'b',{},'err',{});

fname = 'exp2-5-sY-0.1.mat';
foo = load(fname);
all = foo.results;

%figure;
%pidx = 1;
%for j = 1:length(its)
%	it = its(j);
%	subplot(length(its),1,pidx); hold all;
%        for b = bs
%            pee = all(find([all.b] == b));
%            res = [];
%	    cnds = [];
%            for i = 1:length(pee)
%                foo = pee(i).err;
%                res = [res foo(it)];
%	        cnds = [cnds pee(i).kappa];
%            end;
%	    scatter(cnds,log10(res));
%        end;
%	pidx = pidx+1;
%end;
%
%figure;
%pidx = 1;
%for b = bs
%	subplot(1,length(bs),pidx); hold all;
%        pee = all(find([all.b] == b));
%	for j = 1:length(its)
%	    it = its(j);
%            res = [];
%	    cnds = [];
%            for i = 1:length(pee)
%                foo = pee(i).err;
%                res = [res foo(it)];
%	        cnds = [cnds pee(i).kappa];
%            end;
%	    scatter(cnds,log10(res));
%        end;
%	lsline;
%	pidx = pidx+1;
%end;

cnds = []
diffs = [];
for i = 1:length(all)/2
	cnds(end+1) = all(2*i-1).kappa;
	diffs = [diffs; abs(all(2*i-1).err - all(2*i).err)];
end;
figure; hold all;
for i = its
	%scatter(cnds,log10(diffs(:,i)));
	scatter(cnds,diffs(:,i));
end;

