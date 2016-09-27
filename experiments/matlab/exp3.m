clear;

ds = [500];
nsmult = [5];
bs = [0 32 64];
R = 20;
sigmaY = 0.1;
ibits = 4;
ibits = 10;
it = 20;

fname = 'run3-2-%2d-sY-0.1.mat';

for r = 1:R
    results = struct('r',{},'d',{},'nmult',{},'n',{},'kappa',{},'b',{},'err',{});
    for d = ds
        ns = d*nsmult;
        %it = max(ceil(d/2),ceil(2*sqrt(d)));
        % Generate all X's
        nmax = max(ns);
        xall = randn(nmax,d);
        % Scale features
        for i = 1:d
            maxx = max(abs(xall(:,i)));
            xall(:,i) = xall(:,i)/maxx;
        end;
        % Generate parameters
        z = rand(d,1);
        % Generate outputs
        yall = xall*z + sigmaY*randn(nmax,1);
        % Iterate over sample sizes
        for n = ns
            x = xall(1:n,:);
            y = yall(1:n,:);
            xx = x / sqrt(d*n);
            yy = y / sqrt(d*n);
            A = xx'*xx;
            b = xx'*yy;
            %sigmaR = 0.0000;
            sigmaR = (sigmaY^2)/(n*norm(z)^2);
            A = A + sigmaR*eye(d);
            % Iterate over representations
            for bit = bs
                if (bit == 0)
                    T = mytypes('double');
                else
                    % TODO Find the right setting for the entire/fractional
                    % part
                    T = mytypes('fixed',bit,bit-ibits);
                end;
                Afp = cast(A,'like',T);
                bfp = cast(b,'like',T);
                %Xfp = cgdfp(Afp,bfp,it,T);
                Xfp = cgdfp8(Afp,bfp,it,T);
                Xfp2db = double(Xfp);
                err = [];
                for i = 1:it
                    %err(end+1) = norm(z-Xfp2db(:,i));
                    err(end+1) = (norm(x*Xfp2db(:,i) - y)^2)/n + d*sigmaR*norm(Xfp2db(:,i))^2;
                end;
                result.r = r;
                result.d = d;
                result.nmult = n/d;
                result.n = n;
                result.kappa = cond(A);
                result.b = bit;
                result.err = err;
                results(end+1) = result;
            end;
        end;
    end;
    save(sprintf(fname,r),'results');
end;


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
    
% figure;
% subplot(2,2,1); hold all; plot([1:it],err); plot([1:it],errfp);
% subplot(2,2,2); hold all; plot([1:it],res); plot([1:it],resfp);
% subplot(2,2,3); hold all; plot([1:it],log10(err)); plot([1:it],log10(errfp));
% subplot(2,2,4); hold all; plot([1:it],log10(res)); plot([1:it],log10(resfp));
