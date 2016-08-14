clear;

%load('run1-sY-0.1.mat');
% ds = [10 20 50 100 500];
% nsmult = [1 2 5 10 100 500];
% bs = [0 16 32 64];
% R = 1;
% sigmaY = 0.1;

%ds = [20 50 200 500];
%nsmult = [2 5 10 20];
%%nsmult = [2 5 10 20 200];
%%bs = [0 16 32 64];
%bs = [0 32 64];
%its = [10 15 20 40];
%R = 20;
%sigmaY = 0.1;
%fname1 = 'run-%02d-sY-0.1.mat';
%fname = 'run2-%02d-sY-0.1.mat';

ds = [20 50 200 500];
nsmult = [2 5 10 20];
bs = [0 16 32 64];
its = [10 15 20 40];
R = 1;
sigmaY = 0.1;
ibits = 8;
fname = 'run5-%2d-sY-0.1.mat';

titstr = 'd=%d, n=%d, cond=%.2f';
all = struct('r',{},'d',{},'nmult',{},'n',{},'kappa',{},'b',{},'err',{});
for r = 1:R
    %foo = load(sprintf(fname1,r));
    %all = [all foo.results];
    foo = load(sprintf(fname,r));
    all = [all foo.results];
end;

figure;
pidx = 1;
for i = 1:length(ds)
    d = ds(i);
    maxit = its(i);
    foo = all(find([all.d] == d));
    ns = d*nsmult;
    for n = ns
        bar = foo(find([foo.n] == n));
        subplot(4,4,pidx); hold all;
        leg = 'legend(';
        for b = bs
            pee = bar(find([bar.b] == b));
            res = [];
            for i = 1:length(pee)
                res = [res; pee(i).err];
            end;
            leg = [leg sprintf('''%d'',',b)];
            %plot(log2(mean(res(:,1:maxit))));
            plot(log2(res(:,1:maxit)));
            %plot(mean(res(:,1:maxit)));    
            %plot(mean(res));
            %errorbar(mean(log10(res)),std(log10(res)));
        end;
        leg = [leg(1:end-1) ');'];
        avgcond = mean([pee.kappa]);
        title(sprintf(titstr,d,n,avgcond));
        eval(leg);
        pidx = pidx + 1;
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
