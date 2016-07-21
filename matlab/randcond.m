clear;

d = 100;
Cs = [5 10 20 40 80];
R = 20;

exps = [];
avgs = [];

for i = 1:length(Cs)
    C = Cs(i);
    exps(end+1) = (1 + sqrt(1/C))/(1 - sqrt(1/C));
    conds = [];
    for r = 1:R
        X = randn(d,C*d);
        A = X*X';
        conds(end+1) = cond(A);
    end;
    avgs(end+1) = mean(conds);
end;

%figure; hold all; plot(Cs,exps.^2); plot(Cs,avgs);

exps = [];
avgs = [];
sigma = 0.1;

for i = 1:length(Cs)
	C = Cs(i);	
	n = C*d;
	exps(end+1) = ((1 + sqrt(d/n))^2 + 6*sigma^2) / ((1 - sqrt(d/n))^2 + (6*sigma^2));
	conds = [];
	for r = 1:R
		X = randn(d,C*d);
		for j = 1:d
			maxx = max(abs(X(j,:)));
			X(j,:) = X(j,:) / maxx;
		end;
		A = X*X' / (d*n);
		A = A + 6*sigma^2/(n*d) * eye(d);
		conds(end+1) = cond(A);
	end;
	avgs(end+1) = mean(conds);
end;

%figure; hold all; plot(Cs,exps); plot(Cs,avgs);

a = 1.1;
b = 15;
N = 500;
conds = [];
for i = 1:N
	z = (b-a)*rand()+a;
	C = ((z-1)/(z+1))^2 / (1 - sqrt(1 - (1+6*sigma^2)/((z+1)/(z-1))^2))^2;
	n = round(C*d);
	X = randn(d,n);
	for j = 1:d
		maxx = max(abs(X(j,:)));
		X(j,:) = X(j,:) / maxx;
	end;
	A = X*X' / (d*n);
	A = A + 6*sigma^2/(n*d) * eye(d);
	conds(end+1) = cond(A);
end;

hist(conds);
%figure; hold all; plot(Cs,exps); plot(Cs,avgs);


