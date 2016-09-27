clear;

ds = [500];
nsmult = [5];
bs = [0 32 64];
R = 20;
sigmaY = 0.1;
ibits = 4;
ibits = 10;
its = [20];

fname = 'run3-2-%2d-sY-0.1.mat';

all = struct('r',{},'d',{},'nmult',{},'n',{},'kappa',{},'b',{},'err',{});
for r = 1:R
    foo = load(sprintf(fname,r));
    all = [all foo.results];
end;

for i = 1:length(ds)
    d = ds(i);
    maxit = its(i);
    foo = all(find([all.d] == d));
    ns = d*nsmult;
    for n = ns
	figure; hold all;
        bar = foo(find([foo.n] == n));
        for b = bs
            pee = bar(find([bar.b] == b));
            res = [];
            for i = 1:length(pee)
		erri = pee(i).err;
                res = [res; erri];
		%plot(log10(erri(1:maxit)));
            end;
            errorbar(mean(log10(res(:,1:maxit))),std(log10(res(:,1:maxit))));
            %errorbar(mean(res(:,1:maxit)),std(res(:,1:maxit)));
            %plot(log10(res(:,1:maxit)));
            %plot(mean(res(:,1:maxit)));    
            %plot(mean(res));
            %errorbar(mean(log10(res)),std(log10(res)));
        end;
    end;
end;            

% d = 500;
% itn = 50;
% foo = results(find([results.d] == d));
% for b = bs
%     bar = foo(find([foo.b] == b));
%     ks = log10([bar.kappa]);
%     ers = [];
%     for i = 1:length(ks)
%         ers(end+1) = log10(bar(i).err(itn));
%     end;
%     figure;
%     scatter(ks,ers);
% end;

%results = struct('r',{},'d',{},'nmult',{},'n',{},'kappa',{},'b',{},'err',{});

% for n = ns
%     figure; hold all;
%     foo = results(find([results.n] == n));
%     leg = 'legend(';
%     for i = 1:length(foo)
%         plot(log10(foo(i).err));
%         leg = [leg sprintf('''%d'',',foo(i).b)];
%     end;
%     leg = [leg(1:end-1) ');'];
%     title(sprintf('d=%d, n=%d, sY=%f, sR=%f',d,n,sigmaY,sigmaR));
%     eval(leg);
% end;
